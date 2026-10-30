#!/usr/bin/env bash
# Runs once when the RunPod GPU pod starts (plain ubuntu:24.04 image):
# installs ffmpeg, fonts, Python deps and Blender, then starts the job agent.
# Progress goes to /work/boot.log; the agent reports it on /health.
set -euo pipefail
mkdir -p /work
exec > >(tee -a /work/boot.log) 2>&1
echo "[boot] $(date -u) starting"

# The agent must answer health checks while we install, so start it first
# with the system python once that exists.
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 >/dev/null
echo "$AGENT_B64" | base64 -d > /work/pod_agent.py
nohup python3 /work/pod_agent.py > /work/agent.log 2>&1 &

# Self-destruct: the pod deletes itself after POD_MAX_SECONDS even if the driver that started it has
# died (it normally deletes the pod itself, much earlier). RunPod gives every pod its own id and a
# pod-scoped API key in the environment.
if [ -n "${POD_MAX_SECONDS:-}" ]; then
  if [ -n "${RUNPOD_POD_ID:-}" ] && [ -n "${RUNPOD_API_KEY:-}" ]; then
    nohup bash -c "sleep $POD_MAX_SECONDS; echo '[watchdog] time is up, deleting this pod';
      curl -fsS -X DELETE -H \"Authorization: Bearer \$RUNPOD_API_KEY\" https://rest.runpod.io/v1/pods/\$RUNPOD_POD_ID \
      || curl -fsS -X POST -H 'Content-Type: application/json' -H \"Authorization: Bearer \$RUNPOD_API_KEY\" \
           https://rest.runpod.io/v1/pods/\$RUNPOD_POD_ID/stop" >> /work/boot.log 2>&1 &
    echo "[boot] watchdog armed: pod deletes itself in $((POD_MAX_SECONDS / 60)) min"
  else
    echo "[boot] WARNING: no RUNPOD_POD_ID/RUNPOD_API_KEY in the pod; watchdog NOT armed (driver still deletes it)"
  fi
fi

apt-get install -y -qq --no-install-recommends \
  python3-pip ffmpeg fonts-inter curl ca-certificates xz-utils \
  libegl1 libgl1 libglx0 libopengl0 libx11-6 libxi6 libxxf86vm1 libxfixes3 libxrender1 \
  libxkbcommon0 libsm6 libice6 libxext6 libxrandr2 libxcursor1 libxinerama1 libwayland-client0 >/dev/null
echo "[boot] apt done"

if [ "${BOOT_PIP:-1}" = "1" ]; then      # the 2D/TTS pipelines need these; the Blender final render doesn't
  pip install -q --break-system-packages skia-python numpy piper-tts
  echo "[boot] pip done"
fi

# Latest Blender of the requested LTS series (EEVEE Next needs 4.2+).
SERIES="${BLENDER_SERIES:-4.5}"
TARBALL=$(curl -fsSL "https://download.blender.org/release/Blender${SERIES}/" \
  | grep -o "blender-${SERIES}\.[0-9]*-linux-x64\.tar\.xz" | sort -V | tail -1)
echo "[boot] downloading ${TARBALL}"
curl -fsSL "https://download.blender.org/release/Blender${SERIES}/${TARBALL}" | tar -xJ -C /opt
ln -sf /opt/"${TARBALL%.tar.xz}"/blender /usr/local/bin/blender
blender -b --factory-startup --python-expr "import bpy; print('[boot] blender', bpy.app.version_string)" 2>&1 | grep '\[boot\]' || true
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | sed 's/^/[boot] gpu: /' || true
DRV=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -1 | cut -d. -f1)
if [ "${SERIES%%.*}" -ge 5 ] && [ -n "$DRV" ] && [ "$DRV" -lt 575 ]; then
  echo "[boot] WARNING: NVIDIA driver $DRV < 575: Blender ${SERIES} OptiX/CUDA may not render on this host"
fi

# EEVEE needs the NVIDIA EGL (graphics) driver inside the container; without it use Cycles.
if ls /usr/share/glvnd/egl_vendor.d/*nvidia* >/dev/null 2>&1; then
  echo "SHORTS_ENGINE=EEVEE" > /work/engine.env
else
  echo "SHORTS_ENGINE=CYCLES" > /work/engine.env
fi
echo "[boot] engine: $(cat /work/engine.env)"
touch /work/READY
echo "[boot] $(date -u) ready"
wait
