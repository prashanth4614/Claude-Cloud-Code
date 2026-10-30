#!/usr/bin/env bash
# Mac side: answer one Codex question from the cloud session (read-only second opinion).
#   shorts/tools/ask_codex.sh <id>
# Reads shorts/tools/codex/requests/<id>.md, runs `codex exec` read-only in the repo (it can read
# any file, change none), and pushes shorts/tools/codex/answers/<id>.md ending in a STATUS line.
# Model and effort: CODEX_MODEL (default: Codex's configured default), CODEX_EFFORT (default high).
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
ID="${1:?request id}"
BRANCH="claude/youtube-video-production-4ic14n"
REQ="shorts/tools/codex/requests/$ID.md"
ANS="shorts/tools/codex/answers/$ID.md"
git pull --no-rebase -q origin "$BRANCH"
[ -f "$REQ" ] || { echo "no request $REQ"; exit 1; }
MODEL_ARGS=(); [ -n "${CODEX_MODEL:-}" ] && MODEL_ARGS=(--model "$CODEX_MODEL")
T=$(date +%s)
{
  echo "# Codex answer: $ID"
  echo
  echo "_model: ${CODEX_MODEL:-codex default}, reasoning effort: ${CODEX_EFFORT:-high}, read-only_"
  echo
  if codex exec "${MODEL_ARGS[@]}" -c model_reasoning_effort="${CODEX_EFFORT:-high}" \
       --sandbox read-only --skip-git-repo-check "$(cat "$REQ")" 2>/tmp/codex_$ID.err; then
    STATUS=OK
  else
    STATUS=FAILED; echo; echo '```'; tail -30 /tmp/codex_$ID.err; echo '```'
  fi
  echo
  echo "_took $(( $(date +%s) - T )) s_"
  echo "STATUS: ${STATUS}"
} > "$ANS"
git add "$ANS"
git commit -q -m "Codex answer: $ID" || true
git pull --no-rebase -q origin "$BRANCH" && git push -q origin "$BRANCH"
tail -1 "$ANS"
