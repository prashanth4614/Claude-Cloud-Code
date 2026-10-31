#!/usr/bin/env bash
# Wait for the helpers' next push, then exit so the coordinating session wakes up and acts on it.
#   shorts/tools/watch_branch.sh [PATH_REGEX] [MAX_MINUTES]
# Polls origin every 60 s. Exits 0 (printing the new commits and changed files) as soon as the branch
# has a commit that HEAD doesn't, touching a file that matches PATH_REGEX (default: anything). Exits 3
# after MAX_MINUTES (default 120). Run it with the Bash tool's run_in_background: the session is
# re-invoked when it exits. (Scheduled check-ins can't wake this session: see CLAUDE.md, Monitoring.)
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
BRANCH="claude/youtube-video-production-4ic14n"
RE="${1:-.}"
MAX="${2:-120}"
for ((i = 0; i < MAX; i++)); do
  git fetch -q origin "$BRANCH" 2>/dev/null
  new=$(git log --format='%h %s' HEAD..origin/"$BRANCH")
  if [ -n "$new" ]; then
    files=$(git diff --name-only HEAD...origin/"$BRANCH" | grep -E "$RE" || true)
    if [ -n "$files" ]; then
      echo "NEW COMMITS:"; echo "$new"; echo "FILES:"; echo "$files"
      exit 0
    fi
  fi
  sleep 60
done
echo "no matching push in $MAX min"
exit 3
