#!/usr/bin/env python3
"""Render a Short on a rented RunPod GPU, download the MP4, and always delete the pod.

  export RUNPOD_API_KEY=...        # environment secret; never commit it
  python3 cloud/render_runpod.py --out out/ear_pop_3d_cloud.mp4 \
      --include out/ear_pop_3d_work/tts_cache -- \
      python3 shorts/ear_pop_3d.py --voice elevenlabs:<VOICE_ID> --out out/ear_pop_3d_cloud.mp4

Everything after `--` runs on the pod from the repo root. The bundle contains the
git-tracked files plus any --include paths (cached TTS so the pod needs no voice key,
Piper voices, etc.). Cost guard: the pod is deleted on success, failure, Ctrl+C and
after --max-minutes, and the bill is printed at the end.
"""
import argparse
import base64
import io
import json
import os
import secrets
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = os.environ.get("RUNPOD_API_BASE", "https://rest.runpod.io/v1")
POD_URL = os.environ.get("RUNPOD_POD_URL", "https://{id}-8000.proxy.runpod.net")


def http(method, url, body=None, headers=None, raw=False, timeout=120):
    data = body if isinstance(body, (bytes, type(None))) else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out = r.read()
    return out if raw else (json.loads(out) if out else {})


def api(method, path, body=None):
    key = os.environ.get("RUNPOD_API_KEY")
    if not key:
        sys.exit("RUNPOD_API_KEY is not set (add it as an environment secret)")
    try:
        return http(method, API + path, body, {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    except urllib.error.HTTPError as e:
        sys.exit(f"RunPod {method} {path} -> HTTP {e.code}: {e.read().decode()[:500]}")


def bundle(cmd, output, includes, env):
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for f in files:
            if (ROOT / f).is_file() and not f.startswith("shorts/ai/ear_pop/shots/"):
                tf.add(ROOT / f, arcname=f)
        for inc in includes:
            p = (ROOT / inc).resolve()
            if not p.exists():
                sys.exit(f"--include {inc} does not exist")
            tf.add(p, arcname=str(p.relative_to(ROOT)))
        job = json.dumps({"cmd": cmd, "output": output, "env": env}).encode()
        info = tarfile.TarInfo("job.json")
        info.size = len(job)
        tf.addfile(info, io.BytesIO(job))
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="output path (relative to repo) the command writes; downloaded to the same path")
    ap.add_argument("--include", nargs="*", default=[], help="extra files/dirs (inside the repo) to upload")
    ap.add_argument("--gpu", nargs="*", default=["NVIDIA GeForce RTX 4090", "NVIDIA GeForce RTX 5090", "NVIDIA L40S"])
    ap.add_argument("--cloud", default="COMMUNITY", choices=["COMMUNITY", "SECURE"])
    ap.add_argument("--max-minutes", type=float, default=45, help="hard cost guard: delete the pod after this")
    ap.add_argument("--blender-series", default="4.5")
    ap.add_argument("--engine", choices=["auto", "eevee", "cycles"], default="auto",
                    help="auto: EEVEE if the pod has the NVIDIA graphics driver, else Cycles+OptiX")
    ap.add_argument("--dry-run", action="store_true", help="build the bundle and print the plan, no pod")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd[:1] == ["--"] else a.cmd
    if not cmd:
        sys.exit("give the command to run after --")
    data = bundle(cmd, a.out, a.include, {} if a.engine == "auto" else {"SHORTS_ENGINE": a.engine.upper()})
    print(f"bundle: {len(data) / 1e6:.1f} MB, command: {' '.join(cmd)}")
    if a.dry_run:
        return

    token = os.environ.get("RUNPOD_TEST_TOKEN") or secrets.token_urlsafe(24)
    here = Path(__file__).parent
    env = {"JOB_TOKEN": token, "NVIDIA_DRIVER_CAPABILITIES": "all", "BLENDER_SERIES": a.blender_series,
           "BOOT_B64": base64.b64encode((here / "bootstrap.sh").read_bytes()).decode(),
           "AGENT_B64": base64.b64encode((here / "pod_agent.py").read_bytes()).decode()}
    pod = api("POST", "/pods", {
        "name": "shorts-render", "imageName": "ubuntu:24.04", "computeType": "GPU", "gpuCount": 1,
        "gpuTypeIds": a.gpu, "gpuTypePriority": "custom", "cloudType": a.cloud,
        "containerDiskInGb": 40, "volumeInGb": 0, "ports": ["8000/http"], "minRAMPerGPU": 16, "minVCPUPerGPU": 4,
        "env": env, "dockerStartCmd": ["bash", "-c", "echo \"$BOOT_B64\" | base64 -d > /boot.sh && bash /boot.sh"]})
    pid, t0 = pod["id"], time.time()
    rate = pod.get("adjustedCostPerHr") or pod.get("costPerHr") or 0
    gpu = (pod.get("gpu") or {}).get("displayName") or (pod.get("machine") or {}).get("gpuDisplayName") or "GPU"
    print(f"pod {pid}: {gpu} at ${rate}/hr ({a.cloud.lower()} cloud)")
    url, hdr = POD_URL.format(id=pid), {"X-Token": token}
    ok = False
    try:
        deadline = t0 + a.max_minutes * 60
        last_boot = ""
        while True:  # boot: install deps + Blender
            if time.time() > deadline:
                raise TimeoutError("boot exceeded --max-minutes")
            try:
                h = http("GET", url + "/health", timeout=20)
                if h["boot_log"] != last_boot:
                    print("  " + h["boot_log"].splitlines()[-1] if h["boot_log"] else "  booting...", flush=True)
                    last_boot = h["boot_log"]
                if h["ready"]:
                    break
            except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError):
                pass
            time.sleep(float(os.environ.get("RUNPOD_POLL", "10")))
        print(f"ready after {(time.time() - t0) / 60:.1f} min; uploading job")
        http("POST", url + "/job", data, {**hdr, "Content-Type": "application/gzip"}, timeout=300)
        last = None
        while True:
            if time.time() > deadline:
                raise TimeoutError("render exceeded --max-minutes")
            time.sleep(float(os.environ.get("RUNPOD_POLL", "15")))
            try:
                st = http("GET", url + "/status", headers=hdr, timeout=30)
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                continue
            lines = st["log"].splitlines()
            start = len(lines) - 3 if last is None else (len(lines) - lines[::-1].index(last) if last in lines else 0)
            for ln in lines[max(0, start):]:
                print("  | " + ln, flush=True)
            last = lines[-1] if lines else last
            if st["state"] in ("done", "failed"):
                break
        if st["state"] != "done":
            print(f"!! job failed (rc={st['rc']}). Last log lines:\n{st['log']}")
            return
        out = ROOT / a.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(http("GET", url + "/result", headers=hdr, raw=True, timeout=600))
        ok = True
        print(f"downloaded {out} ({out.stat().st_size / 1e6:.1f} MB)")
    finally:
        try:
            api("DELETE", f"/pods/{pid}")
            print(f"pod {pid} deleted")
        except SystemExit as e:
            print(f"!! could not delete pod {pid}: {e}. Delete it in the RunPod console NOW.")
        mins = (time.time() - t0) / 60
        print(f"billed time ~{mins:.1f} min, cost ~${rate * mins / 60:.3f} (~INR {rate * mins / 60 * 88:.0f})")
    return ok


if __name__ == "__main__":
    try:
        sys.exit(0 if main() else 1)
    except (TimeoutError, KeyboardInterrupt) as e:
        sys.exit(f"stopped: {e or 'interrupted'} (pod was deleted)")
