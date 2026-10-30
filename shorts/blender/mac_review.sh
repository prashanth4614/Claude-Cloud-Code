#!/usr/bin/env bash
# Review renders on the Mac (GPU via Metal). One command per job:
#
#   shorts/blender/mac_review.sh <job-name> "<shot specs>" [draft|look]
#   shorts/blender/mac_review.sh sets-v2 all look
#
# Pulls the branch, fetches the free CC0 assets once, builds the film (sets come from the cache
# unless their code changed), runs the QA checks, renders the frames, and commits only the contact
# sheet + legend + log to shorts/pilot_ear_pop/review/mac/<job-name>.*, then pushes.
set -eEuo pipefail
cd "$(git rev-parse --show-toplevel)"

JOB="${1:?job name}"; SHOTS="${2:-all}"; QUALITY="${3:-look}"
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
rm -f "$OUT/$JOB.jpg" "$OUT/$JOB.txt"          # never re-publish a stale sheet
t() { date +%s; }
step() { echo "== $*" | tee -a "$LOG"; }

publish() {   # always push the log (and the sheet if there is one), so the cloud session sees the result
  local status="$1"
  trap - ERR
  echo "STATUS: $status" | tee -a "$LOG"
  git add "$LOG"
  [ -f "$OUT/$JOB.jpg" ] && git add "$OUT/$JOB.jpg" "$OUT/$JOB.txt"
  git commit -q -m "Mac review render: $JOB ($QUALITY) $status" -m "Rendered on the Mac by shorts/blender/mac_review.sh." || true
  git pull --no-rebase -q origin "$BRANCH" && git push -q origin "$BRANCH"
  echo "published $LOG ($status)"
}
trap 'echo "failed at line $LINENO: $BASH_COMMAND" | tee -a "$LOG"; publish FAILED' ERR

T0=$(t)
step "pull"
git pull --no-rebase -q origin "$BRANCH"

step "assets (only downloads what's missing)"
"$BLENDER" -b --factory-startup --python-expr \
  "import runpy, sys; sys.argv = ['fetch']; runpy.run_path('assets/fetch_assets.py', run_name='__main__')" \
  2>&1 | grep -E "^(hdri|polyhaven|ambientcg|  )" | tee -a "$LOG" || true

step "build film"; T=$(t)
"$BLENDER" -b --factory-startup -P shorts/pilot_ear_pop/build_previz.py 2>&1 \
  | grep -E "\[sets\]|\[max\]|\[build\]|Error|Traceback|line [0-9]+" | tee -a "$LOG"
grep -q "\[build\] saved" "$LOG" || false      # no saved .blend = the build failed (trap publishes FAILED)
echo "build: $(( $(t) - T )) s" | tee -a "$LOG"

step "qa"; T=$(t)
"$BLENDER" -b out/pilot_ear_pop/pilot_ear_pop_previz.blend -P shorts/blender/qa_scene.py 2>&1 \
  | grep -E "^\[qa\]|Error|Traceback" | tee -a "$LOG" || true
echo "qa: $(( $(t) - T )) s" | tee -a "$LOG"

step "render ($QUALITY): $SHOTS"; T=$(t)
if [ "$SHOTS" = "all" ]; then SEL=(--all); else SEL=(--shots "$SHOTS"); fi
"$BLENDER" -b out/pilot_ear_pop/pilot_ear_pop_previz.blend -P shorts/blender/review_render.py -- \
  "${SEL[@]}" --quality "$QUALITY" --sheet "$OUT/$JOB.jpg" 2>&1 | grep -E "\[review\]|Error|Traceback" | tee -a "$LOG"
echo "render: $(( $(t) - T )) s" | tee -a "$LOG"
echo "total: $(( $(t) - T0 )) s on $(sysctl -n machdep.cpu.brand_string 2>/dev/null || uname -m)" | tee -a "$LOG"

[ -f "$OUT/$JOB.jpg" ] || false                  # no sheet = the render failed
trap - ERR
publish OK
