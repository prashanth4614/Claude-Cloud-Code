#!/usr/bin/env bash
# Mac side: answer one Codex question from the cloud session (read-only second opinion).
#   shorts/tools/ask_codex.sh <id>
# Reads shorts/tools/codex/requests/<id>.md (with the standing brief shorts/tools/codex/CONTEXT.md
# always prepended, so Codex knows the goal: Zack D Films-style Shorts), runs `codex exec` read-only in the repo (it can read
# any file, change none), and pushes shorts/tools/codex/answers/<id>.md ending in a STATUS line:
#   OK | FAILED (error lines included) | TIMEOUT (partial output included) | REJECTED (bad request)
# Never waits on input: stdin is closed, approvals are off, and a hard cap kills a stuck run.
# A request line "IMAGES: path/a.jpg path/b.jpg" attaches those images (e.g. storyboard sheets).
# Env: CODEX_MODEL (default gpt-6.1-sol), CODEX_EFFORT (default high), CODEX_LIMIT seconds (default 600).
{   # whole script parsed before it runs: a git pull can't change it mid-run
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
source shorts/tools/guard.sh
ID="${1:?request id}"
BRANCH="claude/youtube-video-production-4ic14n"
REQ="shorts/tools/codex/requests/$ID.md"
ANS="shorts/tools/codex/answers/$ID.md"
MODEL="${CODEX_MODEL:-gpt-6.1-sol}"; EFFORT="${CODEX_EFFORT:-high}"; LIMIT="${CODEX_LIMIT:-600}"
take_lock codex
capped 60 git pull --no-rebase -q origin "$BRANCH" || true
OUTF="${TMPDIR:-/tmp}/codex_$ID.out"; ERRF="${TMPDIR:-/tmp}/codex_$ID.err"; LAST="${TMPDIR:-/tmp}/codex_$ID.last"
: > "$OUTF"; : > "$ERRF"; rm -f "$LAST"
T=$(date +%s)
if [ ! -f "$REQ" ]; then
  STATUS=REJECTED; echo "no request file $REQ" > "$ERRF"
elif [ "$(wc -c < "$REQ")" -gt 20000 ]; then
  STATUS=REJECTED; echo "request is $(wc -c < "$REQ") bytes; keep requests under 20 KB" > "$ERRF"
else
  PROMPT="$(cat shorts/tools/codex/CONTEXT.md 2>/dev/null; printf '\n\n---\n\n# This request\n\n'; cat "$REQ")"
  IMG_ARGS=()      # "IMAGES: a.jpg b.jpg" line in the request -> attached as images (repo-relative paths)
  for img in $(grep -m1 '^IMAGES:' "$REQ" | cut -d: -f2-); do
    [ -f "$img" ] && IMG_ARGS+=(--image "$img") || echo "missing image $img" >> "$ERRF"
  done
  capped "$LIMIT" codex exec --model "$MODEL" -c model_reasoning_effort="$EFFORT" -c approval_policy=never \
    --sandbox read-only --skip-git-repo-check --output-last-message "$LAST" ${IMG_ARGS[@]+"${IMG_ARGS[@]}"} "$PROMPT" > "$OUTF" 2> "$ERRF"
  rc=$?
  if [ "$rc" -eq 0 ]; then STATUS=OK; elif [ "$rc" -eq 124 ]; then STATUS=TIMEOUT; else STATUS=FAILED; fi
fi
{
  echo "# Codex answer: $ID"
  echo
  echo "_model: $MODEL, reasoning effort: $EFFORT, read-only, cap ${LIMIT}s_"
  echo
  if [ -s "$LAST" ]; then cat "$LAST"; else cat "$OUTF"; fi
  if [ "$STATUS" != OK ]; then
    echo; echo "**$STATUS**: last lines of Codex's log:"; echo '```'; tail -30 "$ERRF"; echo '```'
  fi
  echo
  echo "_took $(( $(date +%s) - T )) s_"
  echo "STATUS: $STATUS"
} > "$ANS"
git add "$ANS"
git commit -q -m "Codex answer: $ID ($STATUS)" || true
push_with_retry "$BRANCH"
tail -1 "$ANS"
exit
}
