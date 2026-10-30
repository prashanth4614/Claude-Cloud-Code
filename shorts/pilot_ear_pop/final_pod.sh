#!/usr/bin/env bash
# Runs on the RunPod pod (job command): one Blender per GPU over the same frame ranges.
#   final_pod.sh BLEND OUT_DIR [RANGES]
# The workers share the ranges through Blender's placeholders (see render_final.py), so 1 or N GPUs
# need no splitting. Frames already downloaded are listed in OUT_DIR/../done.txt: they get a
# placeholder first and are skipped. Exits non-zero unless every frame in RANGES exists.
set -uo pipefail
BLEND="$1"; OUT="$2"; RANGES="${3:-}"
mkdir -p "$OUT"
if [ -f "$OUT/../done.txt" ]; then
  while read -r n; do [ -n "$n" ] && : > "$OUT/$(printf 'f_%04d.jpg' "$n")"; done < "$OUT/../done.txt"
fi
N=$(nvidia-smi -L 2>/dev/null | wc -l); [ "$N" -ge 1 ] || N=1
nvidia-smi --query-gpu=index,name,driver_version,memory.total --format=csv,noheader || true
echo "[final] $N GPU worker(s), ranges ${RANGES:-all}"
pids=()
for ((i = 0; i < N; i++)); do
  CUDA_VISIBLE_DEVICES=$i blender -b "$BLEND" -P shorts/pilot_ear_pop/render_final.py -- "$OUT" "$RANGES" \
    > "$OUT/../worker_$i.log" 2>&1 &
  pids+=($!)
  sleep 20      # stagger the starts (scene load + BVH build on the CPU)
done
( while :; do sleep 60; grep -h "^\[final\]" "$OUT"/../worker_*.log | tail -2; done ) &
TICK=$!
# black-frame guard: if the first 3 new frames are black (a GPU that renders nothing), stop the workers
# instead of paying for a film of empty frames
(
  seen=0; black=0
  while [ "$seen" -lt 3 ]; do
    sleep 5
    for f in $(find "$OUT" -name 'f_*.jpg' -size +1k -mmin -30 2>/dev/null | sort | head -3); do
      [ -e "$f.checked" ] && continue
      y=$(ffprobe -v error -f lavfi -i "movie=$f,signalstats" -show_entries frame_tags=lavfi.signalstats.YAVG -of csv=p=0 2>/dev/null | head -1)
      : > "$f.checked"; seen=$((seen + 1))
      echo "[final] $(basename "$f") mean level ${y:-?} (of 255)"
      awk -v y="${y:-255}" 'BEGIN{exit !(y < 6)}' && black=$((black + 1))
    done
    if [ "$seen" -ge 3 ] && [ "$black" -ge 3 ]; then
      echo "[final] ERROR: the first frames are black: stopping instead of rendering an empty film"
      pkill -x blender; exit 1
    fi
  done
  rm -f "$OUT"/*.checked
) &
GUARD=$!
rc=0
for p in "${pids[@]}"; do wait "$p" || rc=$?; done
kill "$TICK" "$GUARD" 2>/dev/null; rm -f "$OUT"/*.checked
for f in "$OUT"/../worker_*.log; do echo "--- $f (last 40 lines)"; grep -v "HIPEW" "$f" | tail -40; done
# every frame in the ranges must exist and be non-empty (or be one we already downloaded)
python3 - "$OUT" "$RANGES" <<'EOF'
import sys, pathlib
out, spec = pathlib.Path(sys.argv[1]), sys.argv[2]
done = set()
d = out.parent / "done.txt"
if d.exists():
    done = {int(x) for x in d.read_text().split()}
if not spec:
    spec = f"1-{max(int(p.stem[2:]) for p in out.glob('f_*.jpg'))}"
want = [n for r in spec.split(",") for a, b in [map(int, r.split("-"))] for n in range(a, b + 1)]
missing = [n for n in want if n not in done and (not (out / f"f_{n:04d}.jpg").exists() or (out / f"f_{n:04d}.jpg").stat().st_size == 0)]
print(f"[final] {len(want) - len(missing)}/{len(want)} frames present")
sys.exit(1 if missing else 0)
EOF
ok=$?
[ $ok -eq 0 ] && [ $rc -eq 0 ] && touch "$OUT/../DONE"
exit $(( ok || rc ))
