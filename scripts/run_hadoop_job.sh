#!/usr/bin/env bash
# Runs the word-count job on the Hadoop cluster.
# Run this on the MASTER node after start-dfs.sh and start-yarn.sh.
#
# Usage: ./scripts/run_hadoop_job.sh [local_input_folder]
#        (default input folder: data/)
set -e

cd "$(dirname "$0")/.."
INPUT_LOCAL="${1:-data}"
HDFS_IN=/wordcount/input
HDFS_OUT=/wordcount/output

STREAMING_JAR=$(ls "$HADOOP_HOME"/share/hadoop/tools/lib/hadoop-streaming-*.jar | head -1)
if [ -z "$STREAMING_JAR" ]; then
  echo "Could not find hadoop-streaming jar. Is HADOOP_HOME set?"; exit 1
fi

echo "==> Clearing old HDFS input (the local $INPUT_LOCAL/ folder is the source of truth)"
hdfs dfs -rm -r -f "$HDFS_IN"

echo "==> Uploading $INPUT_LOCAL/*.txt to HDFS $HDFS_IN"
hdfs dfs -mkdir -p "$HDFS_IN"
hdfs dfs -put -f "$INPUT_LOCAL"/*.txt "$HDFS_IN"/
hdfs dfs -ls "$HDFS_IN"

echo "==> Removing old output (if any)"
hdfs dfs -rm -r -f "$HDFS_OUT"

echo "==> Running MapReduce job on YARN"
hadoop jar "$STREAMING_JAR" \
  -D mapreduce.job.name="WordCount-CSBB422" \
  -D mapreduce.job.reduces=2 \
  -files mapreduce/mapper.py,mapreduce/reducer.py \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py" \
  -input "$HDFS_IN" \
  -output "$HDFS_OUT"

echo "==> Fetching results from HDFS into results/wordcount.txt"
mkdir -p results
hdfs dfs -cat "$HDFS_OUT"/part-* > results/wordcount.txt
echo "Done. $(wc -l < results/wordcount.txt) unique words."
echo "Start the dashboard with:  python3 dashboard/app.py"
