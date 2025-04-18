import os
import glob
import json
from collections import defaultdict

from config import OUT_DIR, DATA_DIR

os.makedirs(OUT_DIR, exist_ok=True)

files = glob.glob(os.path.join(DATA_DIR, "*.json"))

by_bible = defaultdict(set)
by_passage = defaultdict(set)
for x in files:
    occ_id = os.path.split(x)[1].replace(".json", "")
    with open(x, "r", encoding="utf-8") as fp:
        data = json.load(fp)
        for item in data:
            try:
                bibl = f'{item["bibl"]} (AI)'
            except:  # noqa:
                continue
            by_bible[bibl].add(occ_id)
            by_passage[occ_id].add(bibl)

serializable_dict = {k: list(v) for k, v in by_bible.items()}
save_path = os.path.join(OUT_DIR, "by_bible.json")
with open(save_path, "w", encoding="utf-8") as fp:
    json.dump(serializable_dict, fp, indent=2)

serializable_dict = {k: list(v) for k, v in by_passage.items()}
save_path = os.path.join(OUT_DIR, "by_passage.json")
with open(save_path, "w", encoding="utf-8") as fp:
    json.dump(serializable_dict, fp, indent=2)


serializable_dict = {}
for x in files:
    occur_id = os.path.split(x)[-1].replace(".json", "")
    with open(x, "r", encoding="utf-8") as fp:
        item = json.load(fp)
        if item:
            serializable_dict[occur_id] = item
save_path = os.path.join(OUT_DIR, "all_in_one.json")

with open(save_path, "w", encoding="utf-8") as fp:
    json.dump(serializable_dict, fp, indent=2)
