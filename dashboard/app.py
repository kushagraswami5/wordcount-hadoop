#!/usr/bin/env python3
"""
Flask dashboard for the Hadoop word-count results.

Features:
  - Top 10 most frequent words and 10 rarest words
  - Basic stats (total words, unique words)
  - Option to hide common English "stop words" (the, and, of ...)
  - Upload new .txt input files and re-run the job from the browser
    (uses the Hadoop cluster if Hadoop is installed, otherwise a local run)

Run:  python3 dashboard/app.py   then open http://localhost:5000
      (other machines on the same network: http://<this-machine-ip>:5000)
"""
import datetime
import glob
import os
import shutil
import subprocess
import sys
import threading

from flask import Flask, jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")
RESULTS_FILE = os.path.join(BASE, "results", "wordcount.txt")
HADOOP_SCRIPT = os.path.join(BASE, "scripts", "run_hadoop_job.sh")
LOCAL_SCRIPT = os.path.join(BASE, "scripts", "run_local_test.py")

STOP_WORDS = set("""
a about above after again against all am an and any are as at be because been
before being below between both but by can did do does doing down during each
few for from further had has have having he her here hers herself him himself
his how if in into is it its itself just me more most my myself no nor not now
of off on once only or other our ours ourselves out over own same she should so
some such than that the their theirs them themselves then there these they this
those through to too under until up very was we were what when where which while
who whom why will with would you your yours yourself yourselves ll re ve don
said one upon could may must shall also
""".split())

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB upload limit

# State of the background job (one job at a time)
job = {"running": False, "engine": None, "log": "", "ok": None, "finished": None}
job_lock = threading.Lock()


# ---------------------------------------------------------------- helpers
def hadoop_available():
    """True if this machine has Hadoop (i.e. it is the cluster master)."""
    return bool(os.environ.get("HADOOP_HOME")) and shutil.which("hdfs") is not None


def human_size(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def list_input_files():
    files = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "*.txt"))):
        files.append({"name": os.path.basename(path), "size": human_size(os.path.getsize(path))})
    total = sum(os.path.getsize(p) for p in glob.glob(os.path.join(DATA_DIR, "*.txt")))
    return files, human_size(total)


def load_counts():
    counts = []
    if not os.path.exists(RESULTS_FILE):
        return counts
    with open(RESULTS_FILE, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 2 and parts[1].isdigit():
                counts.append((parts[0], int(parts[1])))
    return counts


def analyse(hide_stop):
    counts = load_counts()
    pool = [c for c in counts if c[0] not in STOP_WORDS] if hide_stop else counts
    # Most frequent: highest count first, ties broken alphabetically
    top = sorted(pool, key=lambda x: (-x[1], x[0]))[:10]
    # Rarest: lowest count first, ties broken alphabetically
    rare = sorted(counts, key=lambda x: (x[1], x[0]))[:10]
    return {
        "top": top,
        "rare": rare,
        "total_words": sum(c for _, c in counts),
        "unique_words": len(counts),
        "words_seen_once": sum(1 for _, c in counts if c == 1),
        "has_data": bool(counts),
        "results_file": os.path.relpath(RESULTS_FILE, BASE),
        "modified": (
            datetime.datetime.fromtimestamp(os.path.getmtime(RESULTS_FILE)).strftime("%d %b %Y, %H:%M")
            if os.path.exists(RESULTS_FILE) else None
        ),
    }


def run_job_in_background():
    """Runs the MapReduce job (Hadoop or local) and stores its output in `job`."""
    use_hadoop = hadoop_available()
    cmd = ["bash", HADOOP_SCRIPT] if use_hadoop else [sys.executable, LOCAL_SCRIPT]
    with job_lock:
        job.update(running=True, engine="Hadoop cluster (YARN)" if use_hadoop else "Local (no Hadoop)",
                   log="Starting job...\n", ok=None, finished=None)
    try:
        proc = subprocess.Popen(cmd, cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace")
        for line in proc.stdout:
            with job_lock:
                job["log"] += line
        proc.wait()
        ok = proc.returncode == 0
    except Exception as e:  # noqa: BLE001
        with job_lock:
            job["log"] += f"\nERROR: {e}\n"
        ok = False
    with job_lock:
        job.update(running=False, ok=ok, finished=datetime.datetime.now().strftime("%H:%M:%S"))


# ----------------------------------------------------------------- routes
@app.route("/")
def index():
    hide_stop = request.args.get("stop", "1") == "1"
    files, total_size = list_input_files()
    return render_template(
        "index.html", d=analyse(hide_stop), hide_stop=hide_stop,
        files=files, total_size=total_size,
        engine="Hadoop cluster (YARN)" if hadoop_available() else "Local (no Hadoop)",
        msg=request.args.get("msg"),
    )


@app.route("/upload", methods=["POST"])
def upload():
    uploaded = [f for f in request.files.getlist("files") if f and f.filename]
    txt_files = [f for f in uploaded if f.filename.lower().endswith(".txt")]
    if not txt_files:
        return redirect(url_for("index", msg="Please choose at least one .txt file."))

    os.makedirs(DATA_DIR, exist_ok=True)
    if request.form.get("mode") == "replace":
        for old in glob.glob(os.path.join(DATA_DIR, "*.txt")):
            os.remove(old)

    for f in txt_files:
        f.save(os.path.join(DATA_DIR, secure_filename(f.filename)))

    skipped = len(uploaded) - len(txt_files)
    msg = f"Uploaded {len(txt_files)} file(s)."
    if skipped:
        msg += f" Skipped {skipped} file(s) that were not .txt."
    msg += " Now click “Run job”."
    return redirect(url_for("index", msg=msg))


@app.route("/delete/<name>", methods=["POST"])
def delete(name):
    path = os.path.join(DATA_DIR, secure_filename(name))
    if os.path.exists(path):
        os.remove(path)
    return redirect(url_for("index", msg=f"Removed {name}."))


@app.route("/run", methods=["POST"])
def run():
    if job["running"]:
        return jsonify({"started": False, "reason": "A job is already running."})
    if not glob.glob(os.path.join(DATA_DIR, "*.txt")):
        return jsonify({"started": False, "reason": "No input files. Upload a .txt file first."})
    threading.Thread(target=run_job_in_background, daemon=True).start()
    return jsonify({"started": True})


@app.route("/status")
def status():
    with job_lock:
        return jsonify(dict(job))


@app.route("/api/results")
def api():
    return jsonify(analyse(request.args.get("stop", "1") == "1"))


@app.route("/search")
def search():
    q = request.args.get("q", "").strip().lower()
    hit = next((c for w, c in load_counts() if w == q), 0)
    return jsonify({"word": q, "count": hit})


if __name__ == "__main__":
    # host 0.0.0.0 so other machines on the network can open it
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
