#!/usr/bin/env python3
"""
Flask dashboard for the Hadoop word-count results.

Reads results/wordcount.txt (output of the MapReduce job) and shows:
  - Top 10 most frequent words
  - 10 rarest words
  - Basic stats (total words, unique words)
Option: hide common English "stop words" (the, and, of ...) from the top 10.

Run:  python3 dashboard/app.py   then open http://localhost:5000
      (other laptops on the same WiFi: http://<this-laptop-ip>:5000)
"""
import os
from flask import Flask, render_template, request, jsonify

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_FILE = os.path.join(BASE, "results", "wordcount.txt")

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
            __import__("datetime").datetime.fromtimestamp(
                os.path.getmtime(RESULTS_FILE)).strftime("%d %b %Y, %H:%M")
            if os.path.exists(RESULTS_FILE) else None
        ),
    }


@app.route("/")
def index():
    hide_stop = request.args.get("stop", "1") == "1"
    return render_template("index.html", d=analyse(hide_stop), hide_stop=hide_stop)


@app.route("/api/results")
def api():
    return jsonify(analyse(request.args.get("stop", "1") == "1"))


@app.route("/search")
def search():
    q = request.args.get("q", "").strip().lower()
    hit = next((c for w, c in load_counts() if w == q), 0)
    return jsonify({"word": q, "count": hit})


if __name__ == "__main__":
    # host 0.0.0.0 so other laptops on the same network can open it
    app.run(host="0.0.0.0", port=5000, debug=False)
