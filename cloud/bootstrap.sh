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

apt-get install -y -qq --no-install-recommends \
  python3-pip ffmpeg fonts-inter curl ca-certificates xz-utils \
  libegl1 libgl1 libglx0 libopengl0 libx11-6 libxi6 libxxf86vm1 libxfixes3 libxrender1 \
  libxkbcommon0 libsm6 libice6 libxext6 libxrandr2 libxcursor1 libxinerama1 libwayland-client0 >/dev/null
echo "[boot] apt done"

pip install -q --break-system-packages skia-python numpy piper-tts
echo "[boot] pip done"

# Latest Blender of the requested LTS series (EEVEE Next needs 4.2+).
SERIES="${BLENDER_SERIES:-4.5}"
TARBALL=$(curl -fsSL "https://download.blender.org/release/Blender${SERIES}/" \
  | grep -o "blender-${SERIES}\.[0-9]*-linux-x64\.tar\.xz" | sort -V | tail -1)
echo "[boot] downloading ${TARBALL}"
curl -fsSL "https://download.blender.org/release/Blender${SERIES}/${TARBALL}" | tar -xJ -C /opt
ln -sf /opt/"${TARBALL%.tar.xz}"/blender /usr/local/bin/blender
blender -b --factory-startup --python-expr "import bpy; print('[boot] blender', bpy.app.version_string)" 2>&1 | grep '\[boot\]' || true
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader || true

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
