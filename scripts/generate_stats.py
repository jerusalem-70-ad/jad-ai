import glob
import os
import json
from collections import Counter

from config import SUMMARIES_DIR, STATS_DIR, DATA_DIR

os.makedirs(STATS_DIR, exist_ok=True)

print("First, let's generate stats for keywords")
files = glob.glob(f"{SUMMARIES_DIR}/*.json")
items = []
for x in files:
    with open(x, "r", encoding="utf-8") as f:
        data = json.load(f)
        items.extend(data["keywords"])

counter = Counter(items)
data = [
    (key, value) for key, value in counter.items()
]
data.sort(key=lambda x: x[1], reverse=True)
with open(os.path.join(STATS_DIR, "keywords.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

print(f"And the winner is: {data[0]}")

print("and now for the bibl refs")
files = glob.glob(f"{DATA_DIR}/*.json")
items = []
for x in files:
    with open(x, "r", encoding="utf-8") as f:
        data = json.load(f)
        for ref in data:
            try:
                items.append(ref["bibl"])
            except TypeError:
                pass
counter = Counter(items)
data = [
    (key, value) for key, value in counter.items()
]
data.sort(key=lambda x: x[1], reverse=True)
with open(os.path.join(STATS_DIR, "bibl-refs.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

print(f"And the winner is: {data[0]}")
