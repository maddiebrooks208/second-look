#!/usr/bin/env bash
# Replays the demo: three real checks with the local model.
cd "$(dirname "$0")/.."
export SECOND_LOOK_MODEL=${SECOND_LOOK_MODEL:-../../models/gemma-3-1b-it-Q4_K_M.gguf}
for f in 01-reverse-invoice-paypal 09-whatsapp-direct 12-legit-candles; do
  echo "$ second-look check examples/$f.txt"; second-look check examples/$f.txt 2>/dev/null; echo
done
