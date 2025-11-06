#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SRCS=(
  "../boltz/L1000_10/boltz_results_yamls_L1000/predictions"
  "../boltz/L1000_200/boltz_results_yamls_L1000/predictions"
  "../boltz/L3000_10/boltz_results_yamls_L3000/predictions"
  "../boltz/L3000_200/boltz_results_yamls_L3000/predictions"
)

DSTS=(
  "results/affinity_predictions_b0/L1000_10"
  "results/affinity_predictions_b0/L1000_200"
  "results/affinity_predictions_b0/L3000_10"
  "results/affinity_predictions_b0/L3000_200"
)


DRY_RUN=${DRY_RUN:-0}
MOVE=${MOVE:-0}

shopt -s nullglob

for i in "${!SRCS[@]}"; do
  SRC="${SRCS[i]}"
  DST="${DSTS[i]}"

  echo "==> Processing: $SRC  ->  $DST"
  mkdir -p "$DST"

  for dir in "$SRC"/*; do
    [ -d "$dir" ] || continue
    for f in "$dir"/affinity_casp16_*.json; do
      [ -e "$f" ] || continue

      if [ "$DRY_RUN" -eq 1 ]; then
        echo "[DRY RUN] would $( [ "$MOVE" -eq 1 ] && echo 'move' || echo 'copy' ) : \"$f\" -> \"$DST/\""
      else
        if [ "$MOVE" -eq 1 ]; then
          mv -v -- "$f" "$DST/"
        else
          cp -v -- "$f" "$DST/"
        fi
      fi
    done
  done
done

echo "All done."
