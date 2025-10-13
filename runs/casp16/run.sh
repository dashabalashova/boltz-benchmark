#!/usr/bin/env bash
set -euo pipefail

command -v bc >/dev/null 2>&1 || { echo "Please install 'bc' to run this script."; exit 1; }
CONTAINER=${CONTAINER:-boltz2nim}

mkdir -p logs

CSV="logs/boltz_runs_summary.csv"
if [ ! -f "$CSV" ]; then
  echo "name,yaml_dir,sampling_steps,start_ts,end_ts,elapsed_s,py_exit_code,py_log" > "$CSV"
fi

runs=(
  "examples/yamls_L1000 200 L1000"
  "examples/yamls_L1000 10  L1000"
  "examples/yamls_L3000 200 L3000"
  "examples/yamls_L3000 10  L3000"
)

for item in "${runs[@]}"; do
  read -r yaml_dir steps name <<< "$item"
  echo
  echo "=== Run: $name, dir=$yaml_dir, sampling_steps=$steps ==="

  START_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  START_EPOCH=$(date +%s.%N)

  PY_LOG="logs/${name}_b0_py_${steps}.txt"

  echo "Start: $START_TS (epoch=$START_EPOCH)" | tee "$PY_LOG"

  boltz predict "$yaml_dir" --sampling_steps "$steps" --out_dir "${name}_${steps}" 2>&1 | tee -a "$PY_LOG"
  PY_EXIT=$?

  END_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  END_EPOCH=$(date +%s.%N)

  sleep 0.5

  ELAPSED=$(echo "$END_EPOCH - $START_EPOCH" | bc -l)
  
  ELAPSED_FMT=$(printf "%.3f" "$ELAPSED")

  echo "End: $END_TS (epoch=$END_EPOCH); elapsed ${ELAPSED_FMT}s; python exit code: $PY_EXIT"
  
  echo "${name},${yaml_dir},${steps},${START_TS},${END_TS},${ELAPSED_FMT},${PY_EXIT},${PY_LOG}" >> "$CSV"

done

echo
echo "All runs done. Summary saved to $CSV"
