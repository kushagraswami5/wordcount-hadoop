#!/usr/bin/env bash
# Simulates the MapReduce job WITHOUT Hadoop:  cat | map | sort | reduce
# This is exactly what Hadoop Streaming does, just on one machine.
# Use it to test the code on your own laptop, or as a backup during the demo.
set -e
cd "$(dirname "$0")/.."
INPUT_LOCAL="${1:-data}"
mkdir -p results
cat "$INPUT_LOCAL"/*.txt \
  | python3 mapreduce/mapper.py \
  | LC_ALL=C sort \
  | python3 mapreduce/reducer.py > results/wordcount.txt
echo "Done. $(wc -l < results/wordcount.txt) unique words written to results/wordcount.txt"
