#!/usr/bin/env bash
# Downloads a few public-domain books from Project Gutenberg into data/
# so the job has a big dataset to chew on (several MB of text).
set -e
cd "$(dirname "$0")/.."
mkdir -p data
declare -A BOOKS=(
  [pride_and_prejudice]=1342
  [sherlock_holmes]=1661
  [moby_dick]=2701
  [frankenstein]=84
  [alice_in_wonderland]=11
  [war_and_peace]=2600
)
for name in "${!BOOKS[@]}"; do
  id=${BOOKS[$name]}
  echo "Downloading $name ..."
  curl -sL "https://www.gutenberg.org/cache/epub/$id/pg$id.txt" -o "data/$name.txt"
done
ls -lh data
