#!/usr/bin/env python3
"""Tiny job server that runs on the rented GPU pod (stdlib only).

  GET  /health   -> {"ready": bool, "boot_log": tail}        (no auth)
  POST /job      -> body: job.tar.gz with job.json {"cmd": [...], "output": "out/x.mp4"}
  GET  /status   -> {"state": idle|running|done|failed, "rc": int, "log": tail}
  GET  /result   -> the output file
  POST /upload?name=F&part=I   -> appends a chunk to /work/upload/F (part 0 starts the file), so big
                                  files fit under the HTTPS proxy's request size limit
  GET  /frames?dir=D&have=N    -> tar of finished frames in job dir D (non-empty, settled for 3 s)
                                  not yet fetched; the driver pulls them as the render goes
Every endpoint except /health requires the X-Token header to match JOB_TOKEN.
"""
import io
import json
import os
import subprocess
import tarfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WORK = Path(os.environ.get("POD_WORK", "/work"))
JOB = WORK / "job"
TOKEN = os.environ.get("JOB_TOKEN", "")
state = {"state": "idle", "rc": None, "output": None}
UPLOAD = WORK / "upload"
sent = set()          # frames already handed to the driver


def tail(path, n=40):
    try:
        return "\n".join(Path(path).read_text(errors="replace").splitlines()[-n:])
    except FileNotFoundError:
        return ""


def run_job(cmd, output, job_env):
    env = dict(os.environ, BLENDER=os.environ.get("BLENDER", "blender"), PYTHONUNBUFFERED="1")
    detected = WORK / "engine.env"  # written by bootstrap.sh after probing the GPU driver
    if detected.exists():
        k, _, v = detected.read_text().strip().partition("=")
        env[k] = v
    env.update(job_env)
    with open(WORK / "job.log", "w") as log:
        p = subprocess.run(cmd, cwd=JOB, stdout=log, stderr=subprocess.STDOUT, env=env)
    state.update(rc=p.returncode, state="done" if p.returncode == 0 and (JOB / output).exists() else "failed")


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, code, obj=None, body=None, ctype="application/json"):
        data = body if body is not None else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authed(self):
        if TOKEN and self.headers.get("X-Token") == TOKEN:
            return True
        self.reply(403, {"error": "bad token"})
        return False

    def do_GET(self):
        if self.path == "/health":
            gpu = "ok" if (WORK / "GPU_OK").exists() else "bad" if (WORK / "GPU_BAD").exists() else None
            detail = " | ".join(ln for ln in tail(WORK / "boot.log", 40).splitlines() if "gpu" in ln.lower() or "driver" in ln.lower())
            return self.reply(200, {"ready": (WORK / "READY").exists(), "gpu": gpu, "gpu_detail": detail[-600:],
                                    "boot_log": tail(WORK / "boot.log", 6)})
        if not self.authed():
            return
        if self.path == "/status":
            return self.reply(200, dict(state, log=tail(WORK / "job.log")))
        if self.path.startswith("/frames"):
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            d = (JOB / q.get("dir", ["out/final/frames"])[0]).resolve()
            if not str(d).startswith(str(JOB.resolve())) or not d.is_dir():
                return self.reply(200, body=b"", ctype="application/x-tar")
            now, buf, batch = time.time(), io.BytesIO(), []
            for f in sorted(d.glob("*.jpg")):
                st = f.stat()
                if f.name not in sent and st.st_size > 0 and now - st.st_mtime > 3:
                    batch.append(f)
                if len(batch) >= int(q.get("max", ["60"])[0]):
                    break
            with tarfile.open(fileobj=buf, mode="w") as tf:
                for f in batch:
                    tf.add(f, arcname=f.name)
            sent.update(f.name for f in batch)
            return self.reply(200, body=buf.getvalue(), ctype="application/x-tar")
        if self.path == "/result" and state["state"] == "done":
            return self.reply(200, body=(JOB / state["output"]).read_bytes(), ctype="application/octet-stream")
        self.reply(404, {"error": "not found"})

    def do_POST(self):
        if self.path.startswith("/upload"):
            if not self.authed():
                return
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            name = Path(q["name"][0]).name
            UPLOAD.mkdir(parents=True, exist_ok=True)
            data = self.rfile.read(int(self.headers["Content-Length"]))
            with open(UPLOAD / name, "wb" if q["part"][0] == "0" else "ab") as f:
                f.write(data)
            return self.reply(200, {"size": (UPLOAD / name).stat().st_size})
        if self.path != "/job" or not self.authed():
            return
        if not (WORK / "READY").exists():
            return self.reply(409, {"error": "still booting"})
        if state["state"] == "running":
            return self.reply(409, {"error": "job already running"})
        data = self.rfile.read(int(self.headers["Content-Length"]))
        JOB.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
            tf.extractall(JOB, filter="data")
        job = json.loads((JOB / "job.json").read_text())
        state.update(state="running", rc=None, output=job["output"])
        threading.Thread(target=run_job, args=(job["cmd"], job["output"], job.get("env", {})), daemon=True).start()
        self.reply(202, {"accepted": True})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("POD_PORT", "8000"))), H).serve_forever()
