#!/usr/bin/env bash
# Final render of the pilot on RunPod (run from the cloud session or any machine with RUNPOD_API_KEY).
#
#   shorts/pilot_ear_pop/final_render.sh bench [--dry-run]   # 8 frames from each of 7 sets on 1x 4090
#   shorts/pilot_ear_pop/final_render.sh full  [--dry-run]   # every frame, 2x 4090 (falls back to 1)
#   shorts/pilot_ear_pop/final_render.sh assemble            # frames + voice/SFX mix -> MP4 (local)
#   shorts/pilot_ear_pop/final_render.sh diag                # 2 frames + one FILM frame direct, full logs
#
# Builds the film here, packs it into one self-contained .blend (textures, character, sounds inside),
# uploads that, and renders all-Cycles on the pod (render_final.py via final_pod.sh). Frames stream
# back to out/final/<mode>/frames as they finish; a rerun of the same mode skips frames already here.
# The pod is deleted at the end, at the cost guard, and by its own in-pod timer.
# Settings for the full run: FINAL_SAMPLES / FINAL_DENOISER / ... (see render_final.py), from the bench.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
MODE="${1:?bench | full | assemble}"; shift || true
BLENDER="${BLENDER:-$(command -v blender || echo /tmp/claude-0/-home-user-Claude-Cloud-Code/67209568-c2ea-5851-9138-018e925db637/scratchpad/blender/blender-5.2.3-linux-x64/blender)}"
OUT="out/final/$MODE"
mkdir -p "$OUT"
END=$(python3 -c 'import json; print(json.load(open("shorts/pilot_ear_pop/plan.json"))["frame_end"])')

if [ "$MODE" = assemble ]; then
  F=out/final/full/frames
  n=$(find "$F" -name 'f_*.jpg' -size +0 | wc -l)
  [ "$n" -eq "$END" ] || { echo "only $n of $END frames in $F"; exit 1; }
  # the exact voice + SFX mix of the EDIT scene, frame-accurate
  "$BLENDER" -b out/final/film_packed.blend --python-expr "
import bpy
ed = bpy.data.scenes['EDIT']
with bpy.context.temp_override(scene=ed):
    bpy.ops.sound.mixdown(filepath='$PWD/out/final/mix.wav', container='WAV', codec='PCM', format='S16', mixrate=48000)
" 2>&1 | grep -iE "error" || true
  [ -s out/final/mix.wav ] || { echo "audio mixdown failed"; exit 1; }
  ffmpeg -v error -y -framerate 30 -i "$F/f_%04d.jpg" -i out/final/mix.wav \
    -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -c:a aac -b:a 256k -shortest \
    -movflags +faststart out/final/pilot_ear_pop_final.mp4
  echo "-> out/final/pilot_ear_pop_final.mp4"
  exit 0
fi

case "$MODE" in
  bench) RANGES="162-169,372-379,477-484,551-558,628-635,918-925,990-997,1253-1260"; GPUS=1; MAXMIN=35 ;;
  diag)  RANGES="631-631,1256-1256"; GPUS=1; MAXMIN=15; export FINAL_DIAG=631 ;;   # GPU path check, ~2 frames
  full)  RANGES="1-$END"; GPUS=2; MAXMIN="${MAXMIN:-200}" ;;
  *) echo "bench | diag | full | assemble"; exit 1 ;;
esac

# the film, built and packed into one file (only rebuilt when the plan or the code changed)
if [ ! -f out/final/film_packed.blend ] || [ -n "$(find shorts/pilot_ear_pop shorts/blender -name '*.py' -newer out/final/film_packed.blend -o -name '*.json' -newer out/final/film_packed.blend | head -1)" ]; then
  "$BLENDER" -b --factory-startup -P shorts/pilot_ear_pop/build_previz.py 2>&1 | grep -E "\[build\] saved|Error|Traceback"
  "$BLENDER" -b out/pilot_ear_pop/pilot_ear_pop_previz.blend --python-expr "
import bpy
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath='$PWD/out/final/film_packed.blend', compress=True)" >/dev/null 2>&1
fi
[ -s out/final/film_packed.blend ] || { echo "no packed film"; exit 1; }
touch "$OUT/done.txt"

python3 cloud/render_runpod.py --cloud "${RUNPOD_CLOUD:-SECURE}" --gpu-count "$GPUS" --blender-series 5.2 --no-pip --max-minutes "$MAXMIN" \
  --upload out/final/film_packed.blend --pull-frames "$OUT/frames" --include "$OUT/done.txt" \
  --only shorts/pilot_ear_pop/final_pod.sh shorts/pilot_ear_pop/render_final.py \
  --out "$OUT/DONE" "$@" -- \
  bash shorts/pilot_ear_pop/final_pod.sh /work/upload/film_packed.blend "$OUT/frames" "$RANGES"
