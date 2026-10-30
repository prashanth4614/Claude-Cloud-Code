#!/usr/bin/env bash
# Cloud side: wait for the Mac's Codex answer to a request, then print it.
#   shorts/tools/wait_codex.sh <id> [timeout-seconds]      (exit 0 OK, 1 FAILED, 2 timeout)
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
ID="${1:?id}"; LIMIT="${2:-1800}"; BRANCH="claude/youtube-video-production-4ic14n"
ANS="shorts/tools/codex/answers/$ID.md"; start=$(date +%s)
while :; do
  git fetch -q origin "$BRANCH" 2>/dev/null
  if git show "origin/$BRANCH:$ANS" 2>/dev/null | grep -q "^STATUS:"; then
    git pull --no-rebase -q origin "$BRANCH"; cat "$ANS"
    grep -q "^STATUS: OK" "$ANS" && exit 0 || exit 1
  fi
  (( $(date +%s) - start > LIMIT )) && { echo "timeout waiting for $ID"; exit 2; }
  sleep 20
done
