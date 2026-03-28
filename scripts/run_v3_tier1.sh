#!/bin/bash
# run_v3_tier1.sh — Sequential launcher for all Tier 1 papers with _full.md
# Runs one paper at a time, waits for completion, then launches next
# Output goes to reproduction_results_v3/

set -e

PROJECT_ROOT="/home/yjh/Evolution_reproduce"
RESULTS_DIR="$PROJECT_ROOT/data/reproduction_results_v3"
LOGS_DIR="$PROJECT_ROOT/logs/sandbox_stdout"
CLEANUP_SCRIPT="$PROJECT_ROOT/code/utils/sandbox_cleanup.sh"
OPENHANDS_PYTHON="/home/yjh/local_openhands_env/bin/python3"

# Tier 1 papers in order
PAPERS=("pyeit" "pat" "insar" "bpm" "diff")

mkdir -p "$RESULTS_DIR" "$LOGS_DIR"

echo "============================================================"
echo "  Evolution-Reproduce: V3 Tier 1 Sequential Launch"
echo "  Using _full.md (real papers, not code scripts)"
echo "  Results → $RESULTS_DIR"
echo "  Started: $(date)"
echo "============================================================"

for paper in "${PAPERS[@]}"; do
    echo ""
    echo "============================================================"
    echo "  Paper: $paper"
    echo "  Time: $(date)"
    echo "============================================================"
    
    # Cleanup sandbox before each launch
    echo "[1/4] Cleaning sandbox..."
    bash "$CLEANUP_SCRIPT" 2>&1 | tail -5
    sleep 3
    
    # Check if result already exists and is FINISHED
    result_file="$RESULTS_DIR/${paper}_result.json"
    if [ -f "$result_file" ]; then
        state=$(python3 -c "import json; print(json.load(open('$result_file')).get('agent_state',''))" 2>/dev/null || echo "")
        if [[ "$state" == *"FINISHED"* ]]; then
            echo "  ⏭️  $paper already FINISHED in v3, skipping"
            continue
        fi
        echo "  ♻️  Previous result exists (state=$state), will overwrite"
    fi
    
    # Launch using run_baseline.py which creates subprocess
    echo "[2/4] Launching $paper..."
    cd "$PROJECT_ROOT"
    python3 code/baseline/run_baseline.py \
        --markdown "data/paper_markdowns_v2/${paper}_full.md" \
        --paper-id "$paper" \
        --max-iterations 100 2>&1
    
    # run_baseline.py spawns OpenHands as a subprocess and returns immediately
    # Wait for the OpenHands process to finish by monitoring the result file
    echo "[3/4] Waiting for $paper to complete..."
    log_file="$LOGS_DIR/${paper}.log"
    wait_start=$(date +%s)
    max_wait=5400  # 90 min timeout (increased for NFS variability)
    
    while true; do
        elapsed=$(( $(date +%s) - wait_start ))
        
        # Check if result file appeared with final state
        if [ -f "$result_file" ]; then
            state=$(python3 -c "import json; print(json.load(open('$result_file')).get('agent_state',''))" 2>/dev/null || echo "")
            if [[ "$state" == *"FINISHED"* ]] || [[ "$state" == *"ERROR"* ]] || [[ "$state" == *"STOPPED"* ]]; then
                echo "  ✅ $paper completed: state=$state (${elapsed}s)"
                break
            fi
        fi
        
        # Check if OpenHands process is still running (look for session name)
        running=$(ps aux | grep "b2_${paper}_" | grep -v grep | head -1)
        if [ -z "$running" ] && [ $elapsed -gt 120 ]; then
            # Process gone after 2 min - check result
            if [ -f "$result_file" ]; then
                state=$(python3 -c "import json; print(json.load(open('$result_file')).get('agent_state',''))" 2>/dev/null || echo "UNKNOWN")
                echo "  ⚠️  Process ended, state=$state (${elapsed}s)"
            else
                echo "  ❌ Process died without result (${elapsed}s)"
            fi
            break
        fi
        
        # Timeout
        if [ $elapsed -gt $max_wait ]; then
            echo "  ⏰ Timeout after ${elapsed}s, killing..."
            pkill -f "b2_${paper}_" 2>/dev/null || true
            sleep 5
            break
        fi
        
        # Progress report every 2 minutes
        if [ $(( elapsed % 120 )) -lt 15 ] && [ $elapsed -gt 0 ]; then
            logsize=$(wc -c < "$log_file" 2>/dev/null || echo 0)
            # Check process state
            oh_pid=$(ps aux | grep "b2_${paper}_" | grep -v grep | awk '{print $2}' | head -1)
            if [ -n "$oh_pid" ]; then
                pstate=$(cat /proc/$oh_pid/status 2>/dev/null | grep "^State" | awk '{print $2}' || echo "?")
                echo "  ⏳ ${elapsed}s elapsed, log=${logsize}B, pid=$oh_pid state=$pstate"
            else
                echo "  ⏳ ${elapsed}s elapsed, log=${logsize}B, no OH process found"
            fi
        fi
        
        sleep 15
    done
    
    # Summary for this paper
    echo "[4/4] Result for $paper:"
    if [ -f "$result_file" ]; then
        python3 -c "
import json
d = json.load(open('$result_file'))
print(f\"  State: {d.get('agent_state', '?')}\")
print(f\"  Iterations: {d.get('iterations_used', '?')}\")
print(f\"  Elapsed: {d.get('elapsed_seconds', '?')}s\")
print(f\"  Has results.json: {d.get('has_results_json', '?')}\")
" 2>/dev/null || echo "  (could not parse result)"
    else
        echo "  No result file generated"
    fi
    
    echo ""
    sleep 5  # Brief pause between papers
done

echo ""
echo "============================================================"
echo "  ALL TIER 1 PAPERS COMPLETE"
echo "  Time: $(date)"
echo "============================================================"
echo ""

# Final summary
echo "=== FINAL SUMMARY ==="
for paper in "${PAPERS[@]}"; do
    result_file="$RESULTS_DIR/${paper}_result.json"
    if [ -f "$result_file" ]; then
        python3 -c "
import json
d = json.load(open('$result_file'))
state = d.get('agent_state', '?')
has_r = '✅' if d.get('has_results_json') else '❌'
elapsed = d.get('elapsed_seconds', 0)
icon = '✅' if 'FINISHED' in str(state) else '❌'
print(f'  {icon} $paper: {state} | results.json={has_r} | {elapsed:.0f}s')
" 2>/dev/null || echo "  ❓ $paper: parse error"
    else
        echo "  ❌ $paper: no result"
    fi
done
