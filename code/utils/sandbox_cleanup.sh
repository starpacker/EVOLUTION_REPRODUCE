#!/bin/bash
# Comprehensive sandbox cleanup script
# Kills ALL orphaned sandbox processes (action_execution_server, jupyter, tmux children)
# Usage: bash sandbox_cleanup.sh [--force]

FORCE=${1:-""}

echo "=== Sandbox Cleanup ==="
echo "Time: $(date)"

# 1. Kill all action_execution_server processes and their children
echo ""
echo "Step 1: Killing action_execution_server process trees..."
pids=$(pgrep -f "action_execution_server" 2>/dev/null)
if [ -n "$pids" ]; then
    for pid in $pids; do
        echo "  Killing process tree for PID $pid"
        # Kill the entire process group
        kill -9 -$(ps -o pgid= -p $pid 2>/dev/null | tr -d ' ') 2>/dev/null
        kill -9 $pid 2>/dev/null
    done
else
    echo "  No action_execution_server processes found"
fi

# 2. Kill all run_evolution_task processes
echo ""
echo "Step 2: Killing run_evolution_task processes..."
pids=$(pgrep -f "run_evolution_task" 2>/dev/null)
if [ -n "$pids" ]; then
    for pid in $pids; do
        echo "  Killing PID $pid"
        kill -9 $pid 2>/dev/null
    done
else
    echo "  No run_evolution_task processes found"
fi

# 3. Kill orphaned python3.12 processes listening on sandbox port range (30000-39999)
echo ""
echo "Step 3: Killing orphaned python3.12 listeners on ports 30000-39999..."
orphan_pids=$(ss -tlnp 2>/dev/null | grep -E ':3[0-9]{4}\b' | grep python3.12 | grep -oP 'pid=\K[0-9]+' | sort -un)
if [ -n "$orphan_pids" ]; then
    for pid in $orphan_pids; do
        echo "  Killing orphan PID $pid"
        kill -9 $pid 2>/dev/null
    done
else
    echo "  No orphaned listeners found"
fi

# 4. Clean up stale tmux sessions from sandbox
echo ""
echo "Step 4: Cleaning stale tmux sessions..."
tmux_sessions=$(tmux list-sessions 2>/dev/null | grep -v attached | cut -d: -f1)
if [ -n "$tmux_sessions" ]; then
    for sess in $tmux_sessions; do
        echo "  Killing tmux session: $sess"
        tmux kill-session -t "$sess" 2>/dev/null
    done
else
    echo "  No stale tmux sessions found"
fi

# 5. Clean up temp workspaces
if [ "$FORCE" = "--force" ]; then
    echo ""
    echo "Step 5: Cleaning temp workspaces..."
    rm -rf /tmp/openhands_workspace_* 2>/dev/null
    echo "  Temp workspaces cleaned"
fi

echo ""
echo "=== Cleanup Complete ==="
echo "Remaining action_execution_server: $(pgrep -fc action_execution_server 2>/dev/null || echo 0)"
echo "Remaining listeners on 30000-39999: $(ss -tlnp 2>/dev/null | grep -cE ':3[0-9]{4}\b' || echo 0)"
