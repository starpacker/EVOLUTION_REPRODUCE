#!/bin/bash
# monitor_v3.sh — Quick status check for V3 Tier 1 runs
# Usage: bash scripts/monitor_v3.sh

PROJECT_ROOT="/home/yjh/Evolution_reproduce"
RESULTS_DIR="$PROJECT_ROOT/data/reproduction_results_v3"
LOGS_DIR="$PROJECT_ROOT/logs/sandbox_stdout"

echo "=== V3 Tier 1 Monitor — $(date) ==="
echo ""

# Check if launcher is running
launcher_pid=$(pgrep -f "run_v3_tier1" 2>/dev/null | head -1)
if [ -n "$launcher_pid" ]; then
    echo "🟢 Launcher running (PID $launcher_pid)"
else
    echo "⚪ Launcher not running"
fi

# Check for OpenHands processes
oh_pids=$(pgrep -f "run_evolution_task" 2>/dev/null)
if [ -n "$oh_pids" ]; then
    for pid in $oh_pids; do
        state=$(cat /proc/$pid/status 2>/dev/null | grep "^State" | awk '{print $2}')
        rss=$(cat /proc/$pid/status 2>/dev/null | grep "^VmRSS" | awk '{print $2}')
        etime=$(ps -p $pid -o etime= 2>/dev/null | tr -d ' ')
        cmd=$(ps -p $pid -o args= 2>/dev/null | grep -o 'session-name [^ ]*' | awk '{print $2}')
        echo "  🔄 PID $pid: state=$state rss=${rss}kB elapsed=$etime session=$cmd"
    done
else
    echo "  No OpenHands processes running"
fi

echo ""
echo "=== Results ==="
PAPERS=("pyeit" "pat" "insar" "bpm" "diff")
for paper in "${PAPERS[@]}"; do
    result_file="$RESULTS_DIR/${paper}_result.json"
    log_file="$LOGS_DIR/${paper}.log"
    
    if [ -f "$result_file" ]; then
        python3 -c "
import json
d = json.load(open('$result_file'))
state = d.get('agent_state', '?')
has_r = '✅' if d.get('has_results_json') else '❌'
elapsed = d.get('elapsed_seconds', 0)
iters = d.get('iterations_used', '?')
icon = '✅' if 'FINISHED' in str(state) else ('❌' if 'ERROR' in str(state) else '🔄')
print(f'{icon} {\"$paper\":8s}: {state} | iters={iters} | results.json={has_r} | {elapsed:.0f}s')
" 2>/dev/null || echo "❓ $paper: parse error"
    else
        logsize=$(wc -c < "$log_file" 2>/dev/null || echo 0)
        if [ "$logsize" -gt 0 ] 2>/dev/null; then
            echo "🔄 ${paper}    : running (log=${logsize}B)"
        else
            echo "⬜ ${paper}    : not started"
        fi
    fi
done

echo ""
echo "=== Launcher Log (last 5 lines) ==="
tail -5 "$PROJECT_ROOT/logs/v3_tier1_launch.log" 2>/dev/null || echo "(no launcher log)"
