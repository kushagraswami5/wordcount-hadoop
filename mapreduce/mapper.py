#!/usr/bin/env python3
"""
Mapper for Hadoop Streaming word count.

Input : lines of raw text on stdin (Hadoop feeds each split line by line)
Output: "word<TAB>1" for every word found

Cleaning rules:
  - lowercase everything
  - keep only letters a-z (numbers / punctuation are dropped)
  - ignore 1-letter tokens (like "a", "s" from "it's") to reduce noise
"""
import re
import sys

WORD_RE = re.compile(r"[a-z]+")

for line in sys.stdin:
    for word in WORD_RE.findall(line.lower()):
        if len(word) > 1:
            print(f"{word}\t1")
