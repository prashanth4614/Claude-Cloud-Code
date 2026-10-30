#!/usr/bin/env bash
# Cloud side: wait (cheaply) for a Mac review job to publish its result, then print its log.
#   shorts/blender/wait_mac_job.sh <job-name> [timeout-seconds]
# Polls GitHub every 20 s for shorts/pilot_ear_pop/review/mac/<job>.log; exits 0 on STATUS: OK,
# 1 on STATUS: FAILED, 2 on timeout.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
JOB="${1:?job name}"; LIMIT="${2:-2400}"
BRANCH="claude/youtube-video-production-4ic14n"
LOG="shorts/pilot_ear_pop/review/mac/$JOB.log"
start=$(date +%s)
while :; do
  git fetch -q origin "$BRANCH" 2>/dev/null
  if git cat-file -e "origin/$BRANCH:$LOG" 2>/dev/null && git show "origin/$BRANCH:$LOG" | grep -q "^STATUS:"; then
    git pull --no-rebase -q origin "$BRANCH"
    cat "$LOG"
    grep -q "^STATUS: OK" "$LOG" && exit 0 || exit 1
  fi
  (( $(date +%s) - start > LIMIT )) && { echo "timeout waiting for $JOB"; exit 2; }
  sleep 20
done
