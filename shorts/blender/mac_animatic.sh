#!/usr/bin/env bash
# Animatic (Gate B) on the Mac: the whole film, every frame, 540x960, with the voice when it's on the Mac.
# EEVEE by default (~85 min); ANIMATIC_ENGINE=WORKBENCH for a flat preview in minutes.
#
#   shorts/blender/mac_animatic.sh <job-name> [frames]      e.g.  animatic-test 30   |   animatic-1
#
# The voice isn't in git, so the Mac renders a silent MP4; the cloud session adds the voice/SFX mix.
# Test the script itself without pushing anything: NO_PUBLISH=1 BLENDER=/path/to/blender ...
# Pulls the branch, fetches the free CC0 assets once, builds the film (sets come from the cache
# unless their code changed), runs the QA checks, renders the frames, and commits only the contact
# sheet + legend + log to shorts/pilot_ear_pop/review/mac/<job-name>.*, then pushes.
{   # whole script parsed before it runs: a git pull can't change it mid-run
set -eEuo pipefail
cd "$(git rev-parse --show-toplevel)"
source shorts/tools/guard.sh
take_lock render

JOB="${1:?job name}"; FRAMES="${2:-}"; QUALITY="animatic ${ANIMATIC_ENGINE:-EEVEE}"
BRANCH="claude/youtube-video-production-4ic14n"
BLENDER="${BLENDER:-}"
for b in "$BLENDER" /Applications/Blender.app/Contents/MacOS/Blender "$HOME/Applications/Blender.app/Contents/MacOS/Blender"; do
  [ -n "$b" ] && [ -x "$b" ] && BLENDER="$b" && break
done
[ -x "$BLENDER" ] || { echo "Blender not found: set BLENDER=/path/to/Blender"; exit 1; }

OUT=shorts/pilot_ear_pop/review/mac
mkdir -p "$OUT"
LOG="$OUT/$JOB.log"
: > "$LOG"
rm -f "$OUT/$JOB.mp4"                          # never re-publish a stale video
t() { date +%s; }
step() { echo "== $*" | tee -a "$LOG"; }

publish() {   # always push the log (and the sheet if there is one), so the cloud session sees the result
  local status="$1"
  trap - ERR
  echo "STATUS: $status" | tee -a "$LOG"
  if [ -n "${NO_PUBLISH:-}" ]; then echo "NO_PUBLISH set: not committing ($status)"; return 0; fi
  git add "$LOG"
  [ -f "$OUT/$JOB.mp4" ] && git add -f "$OUT/$JOB.mp4"   # *.mp4 is gitignored; review animatics are the exception
  git commit -q -m "Mac review render: $JOB ($QUALITY) $status" -m "Rendered on the Mac by shorts/blender/mac_animatic.sh." || true
  push_with_retry "$BRANCH" || true
  echo "published $LOG ($status)"
}
trap 'echo "failed at line $LINENO: $BASH_COMMAND" | tee -a "$LOG"; publish FAILED' ERR
# Never waits on input: stdin is closed for every step, and every step has a hard time cap
# (assets 15 min, build 15 min, render RENDER_LIMIT or 100 min).

T0=$(t)
step "pull"
capped 120 git pull --no-rebase -q origin "$BRANCH"

step "assets (only downloads what's missing)"
capped 900 "$BLENDER" -b --factory-startup --python-expr \
  "import runpy, sys; sys.argv = ['fetch']; runpy.run_path('assets/fetch_assets.py', run_name='__main__')" \
  > out/assets_$JOB.txt 2>&1 || echo "asset fetch exit $?" | tee -a "$LOG"
grep -E "^(hdri|polyhaven|ambientcg|  )" out/assets_$JOB.txt | tee -a "$LOG" || true

step "build film"; T=$(t)
capped 900 "$BLENDER" -b --factory-startup -P shorts/pilot_ear_pop/build_previz.py > out/build_$JOB.txt 2>&1 \
  || echo "build exit $? (124 = hit the 15 min cap)" | tee -a "$LOG"
grep -E "\[sets\]|\[max\]|\[build\]|Error|Traceback|line [0-9]+" out/build_$JOB.txt | tee -a "$LOG" || true
grep -q "\[build\] saved" "$LOG" || false      # no saved .blend = the build failed (trap publishes FAILED)
echo "build: $(( $(t) - T )) s" | tee -a "$LOG"

step "render animatic${FRAMES:+ (first $FRAMES frames)}"; T=$(t)
RAW="out/animatic_$JOB.txt"
# default cap 100 min: the full film takes ~85 min at 4 samples on the M4
RC=0
capped "${RENDER_LIMIT:-6000}" "$BLENDER" -b out/pilot_ear_pop/pilot_ear_pop_previz.blend \
  -P shorts/pilot_ear_pop/render_animatic.py -- "$PWD/$OUT/$JOB.mp4" 50 $FRAMES > "$RAW" 2>&1 || RC=$?
# a killed Blender leaves an MP4 without its index (unplayable): never publish that as OK
[ "$RC" -eq 0 ] || { echo "blender exit code $RC (124 = hit the render cap, 143 = terminated)" | tee -a "$LOG"; rm -f "$OUT/$JOB.mp4"; }
grep -E "\[animatic\]|Error|Traceback|Append frame|Fra:1 " "$RAW" | tail -5 | tee -a "$LOG" || true
[ -f "$OUT/$JOB.mp4" ] || { echo "-- last 40 lines of Blender output:" >> "$LOG"; tail -40 "$RAW" >> "$LOG"; }
N="${FRAMES:-$(python3 -c 'import json; print(json.load(open("shorts/pilot_ear_pop/plan.json"))["frame_end"])' 2>/dev/null || echo 1)}"
SECS=$(( $(t) - T ))
# (no ">" inside awk's printf: awk reads it as an output redirect, which is why this printed blank)
echo "render: $SECS s for $N frames ($(awk -v s="$SECS" -v n="$N" 'BEGIN{if (n < 1) n = 1; printf "%.2f", s / n}') s/frame)" | tee -a "$LOG"
echo "size: $(du -h "$OUT/$JOB.mp4" 2>/dev/null | cut -f1)" | tee -a "$LOG"
echo "total: $(( $(t) - T0 )) s on $(sysctl -n machdep.cpu.brand_string 2>/dev/null || uname -m)" | tee -a "$LOG"

[ -f "$OUT/$JOB.mp4" ] || false                  # no video = the render failed
trap - ERR
publish OK
exit
}
