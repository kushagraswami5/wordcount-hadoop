#!/usr/bin/env python3
"""
Runs the word-count job WITHOUT Hadoop, on Windows, Mac or Linux.
It does the same thing as Hadoop Streaming:  mapper -> sort -> reducer

Usage:  python scripts/run_local_test.py
"""
import glob
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)

files = glob.glob(os.path.join("data", "*.txt"))
if not files:
    sys.exit("No .txt files found in the data folder.")

text = ""
for f in files:
    with open(f, encoding="utf-8", errors="ignore") as fh:
        text += fh.read() + "\n"

# 1. Map
mapped = subprocess.run([sys.executable, "mapreduce/mapper.py"], input=text,
                        capture_output=True, text=True, encoding="utf-8", check=True).stdout
# 2. Shuffle & sort (Hadoop does this step for us on the cluster)
sorted_lines = "\n".join(sorted(mapped.splitlines())) + "\n"
# 3. Reduce
reduced = subprocess.run([sys.executable, "mapreduce/reducer.py"], input=sorted_lines,
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout

os.makedirs("results", exist_ok=True)
with open(os.path.join("results", "wordcount.txt"), "w", encoding="utf-8", newline="\n") as out:
    out.write(reduced)

print(f"Read {len(files)} file(s). {len(reduced.splitlines())} unique words "
      f"written to results/wordcount.txt")
print("Now start the dashboard:  python dashboard/app.py")
