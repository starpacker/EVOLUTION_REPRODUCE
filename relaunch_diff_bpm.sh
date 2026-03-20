#!/bin/bash
# Relaunch DIFF (API errors wasted all iterations) and BPM (sandbox ConnectError)
cd /home/yjh/Evolution_reproduce

TS=$(date +%Y%m%d_%H%M%S)

echo "=== Launching DIFF at $TS ==="
nohup /data/yjh/conda_envs/openhands/bin/python3 /home/yjh/OpenHands/run_evolution_task.py \
  --prompt-file /home/yjh/Evolution_reproduce/data/agent_prompts_v2/diff_prompt.txt \
  --workspace /data/yjh/openhands_workspace/tier1_v2_diff_${TS} \
  --session-name tier1_v2_diff_${TS} \
  --max-iterations 100 \
  --config /home/yjh/OpenHands/config.toml \
  --output-file /home/yjh/Evolution_reproduce/data/reproduction_results_v2/diff_result.json \
  > /home/yjh/Evolution_reproduce/logs/sandbox_stdout/diff.log 2>&1 &
echo "DIFF PID: $!"

echo "Waiting 60s before launching BPM..."
sleep 60

TS2=$(date +%Y%m%d_%H%M%S)
echo "=== Launching BPM at $TS2 ==="
nohup /data/yjh/conda_envs/openhands/bin/python3 /home/yjh/OpenHands/run_evolution_task.py \
  --prompt-file /home/yjh/Evolution_reproduce/data/agent_prompts_v2/bpm_prompt.txt \
  --workspace /data/yjh/openhands_workspace/tier1_v2_bpm_${TS2} \
  --session-name tier1_v2_bpm_${TS2} \
  --max-iterations 100 \
  --config /home/yjh/OpenHands/config.toml \
  --output-file /home/yjh/Evolution_reproduce/data/reproduction_results_v2/bpm_result.json \
  > /home/yjh/Evolution_reproduce/logs/sandbox_stdout/bpm.log 2>&1 &
echo "BPM PID: $!"

echo "=== Both launched ==="
