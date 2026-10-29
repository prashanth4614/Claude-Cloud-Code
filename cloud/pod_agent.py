#!/usr/bin/env python3
"""Tiny job server that runs on the rented GPU pod (stdlib only).

  GET  /health   -> {"ready": bool, "boot_log": tail}        (no auth)
  POST /job      -> body: job.tar.gz with job.json {"cmd": [...], "output": "out/x.mp4"}
  GET  /status   -> {"state": idle|running|done|failed, "rc": int, "log": tail}
  GET  /result   -> the output file
Every endpoint except /health requires the X-Token header to match JOB_TOKEN.
"""
import io
import json
import os
import subprocess
import tarfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WORK = Path(os.environ.get("POD_WORK", "/work"))
JOB = WORK / "job"
TOKEN = os.environ.get("JOB_TOKEN", "")
state = {"state": "idle", "rc": None, "output": None}


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
            return self.reply(200, {"ready": (WORK / "READY").exists(), "boot_log": tail(WORK / "boot.log", 6)})
        if not self.authed():
            return
        if self.path == "/status":
            return self.reply(200, dict(state, log=tail(WORK / "job.log")))
        if self.path == "/result" and state["state"] == "done":
            return self.reply(200, body=(JOB / state["output"]).read_bytes(), ctype="application/octet-stream")
        self.reply(404, {"error": "not found"})

    def do_POST(self):
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
