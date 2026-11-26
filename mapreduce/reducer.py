#!/usr/bin/env python3
"""
Reducer for Hadoop Streaming word count.

Hadoop sorts mapper output by key before it reaches the reducer, so all
lines for the same word arrive one after another. We just add up the 1s
until the word changes.

Input : "word<TAB>1" lines, sorted by word
Output: "word<TAB>total_count"
"""
import sys

current_word = None
current_count = 0

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        word, count = line.split("\t", 1)
        count = int(count)
    except ValueError:
        continue  # skip malformed lines

    if word == current_word:
        current_count += count
    else:
        if current_word is not None:
            print(f"{current_word}\t{current_count}")
        current_word = word
        current_count = count

if current_word is not None:
    print(f"{current_word}\t{current_count}")
