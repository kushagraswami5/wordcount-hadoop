# Word Count with Hadoop MapReduce

**CSBB 422 – Big Data Analytics · Lab Project 1**

This project counts how often each word appears in a large text dataset, using a Hadoop
MapReduce job that runs on a 3-node cluster (1 master and 2 workers). A web dashboard then
shows the **10 most frequent** and **10 rarest** words.

```
 text files ──► HDFS ──► MapReduce on YARN (mapper.py → shuffle/sort → reducer.py)
                                  │
                         /wordcount/output in HDFS
                                  │
                       results/wordcount.txt ──► Flask dashboard (port 5000)
```

## Project structure
```
mapreduce/mapper.py        emits  word<TAB>1  for every word
mapreduce/reducer.py       adds up the counts for each word
scripts/get_books.sh       downloads Gutenberg books into data/ (big dataset)
scripts/run_hadoop_job.sh  uploads data to HDFS, runs the job, fetches results
scripts/run_local_test.sh  same job without Hadoop (for testing and as a backup)
dashboard/app.py           Flask web UI
configs/                   Hadoop config files for the 3-laptop cluster
docs/CLUSTER_SETUP.md      step-by-step cluster setup
```

---

## Moving the project from my laptop to my friend's laptop

The code lives on GitHub, so any laptop can download it with one command.
GitHub is also required for submission.

**On my laptop (once):**
```bash
cd wordcount-hadoop
git init
git add .
git commit -m "Word count with Hadoop MapReduce"
git branch -M main
git remote add origin https://github.com/<your-username>/wordcount-hadoop.git
git push -u origin main
```
After any later change: `git add . && git commit -m "update" && git push`

**On my friend's laptop:**
```bash
git clone https://github.com/<your-username>/wordcount-hadoop.git
cd wordcount-hadoop
pip install -r requirements.txt
```
To get later updates: `git pull`

The `results/` and `data/` folders are not uploaded to GitHub, apart from the small sample.
Regenerate them on the demo laptop by running the job there.

---

## Running it

### A. Quick test (any laptop, no Hadoop needed)
```bash
pip install -r requirements.txt
python scripts/run_local_test.py   # works on Windows, Mac, Linux
python3 dashboard/app.py         # open http://localhost:5000
```

### B. The real thing: on the Hadoop cluster
First set up the cluster by following [docs/CLUSTER_SETUP.md](docs/CLUSTER_SETUP.md). Then, on the **master**:
```bash
start-dfs.sh && start-yarn.sh
./scripts/get_books.sh           # optional: download about 6 books (several MB)
./scripts/run_hadoop_job.sh      # runs the MapReduce job across the 2 workers
python3 dashboard/app.py         # dashboard on http://master:5000
```

---

## Demo script (for the evaluation)

1. **Show the cluster is live**
   - `jps` on the master and `ssh worker1 jps` for the workers
   - `hdfs dfsadmin -report` shows "Live datanodes (2)"
   - Open http://master:9870 (Datanodes tab) and http://master:8088
2. **Basic HDFS commands**
   ```bash
   hdfs dfs -ls /wordcount/input
   hdfs dfs -du -h /wordcount/input
   hdfs fsck /wordcount/input -files -blocks -locations   # blocks spread across workers
   ```
3. **Run the job** with `./scripts/run_hadoop_job.sh`, then show it running at http://master:8088
4. **Show the raw output** with `hdfs dfs -cat /wordcount/output/part-00000 | head`
5. **Open the dashboard**: top 10, rarest 10, the stop-word toggle and word search

## How it works (for the viva)
- **Map:** each mapper gets a chunk (split) of the input, lowercases it, extracts words
  and prints `word 1` for each one.
- **Shuffle and sort:** Hadoop groups all identical words together and sorts them by key.
  It also sends each word to a reducer (2 reducers here, so the work is split).
- **Reduce:** the reducer reads the sorted stream and adds up the 1s for each word.
- **Hadoop Streaming** lets us write the mapper and reducer in Python. They read from
  stdin and write to stdout.
- **Rarest words:** many words appear only once, so we break ties alphabetically.
- **Stop words** ("the", "and", "of" and so on) can be hidden from the top 10, because
  otherwise they dominate the list.
