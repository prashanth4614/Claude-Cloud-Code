# Shared guards for the Mac helper scripts (sourced, not run).
#   capped <seconds> <cmd...>   run a command with a hard time cap (macOS has no `timeout`);
#                               returns 124 when it had to be killed
#   push_with_retry <branch>    pull --no-rebase + push, retried with back-off (2, 4, 8, 16 s)
#   take_lock <name>            one job at a time per checkout (waits up to 30 min for the previous one)

capped() {   # safe under `set -eE` + ERR traps: nothing in here returns non-zero by accident
  local limit="$1"; shift
  local mark rc=0 pid dog
  mark="$(mktemp "${TMPDIR:-/tmp}/capped.XXXXXX")" && rm -f "$mark"
  "$@" < /dev/null &
  pid=$!
  ( sleep "$limit" && touch "$mark" && kill -TERM "$pid" 2>/dev/null && sleep 10 && kill -KILL "$pid" 2>/dev/null ) &
  dog=$!
  wait "$pid" || rc=$?
  pkill -P "$dog" sleep 2>/dev/null || true   # its sleep too, or it lingers as an orphan
  kill "$dog" 2>/dev/null || true
  wait "$dog" 2>/dev/null || true
  if [ -e "$mark" ]; then rm -f "$mark"; rc=124; fi
  return "$rc"
}

push_with_retry() {
  local branch="$1" d
  for d in 0 2 4 8 16; do
    sleep "$d"
    git pull --no-rebase -q origin "$branch" && git push -q origin "$branch" && return 0
    git merge --abort 2>/dev/null || true
  done
  echo "push failed after retries (result kept locally)"; return 1
}

take_lock() {
  local lock="${TMPDIR:-/tmp}/shorts-$1.lock" waited=0
  while ! mkdir "$lock" 2>/dev/null; do
    if [ "$waited" -ge 1800 ]; then echo "lock $lock held for 30 min; taking it over"; rm -rf "$lock"; continue; fi
    sleep 10; waited=$((waited + 10))
  done
  trap 'rm -rf "'"$lock"'"' EXIT
}
