from collections import defaultdict
import os
import pandas as pd
from config import OUT_DIR
from acdh_bible_pyutils import get_book_from_bibl_ref
from csae_pyutils import save_json, load_json

source_data = load_json(os.path.join(OUT_DIR, "all_in_one_backup.json"))

ai_refs_old = defaultdict(list)
for key, value in source_data.items():
    for y in value:
        try:
            bibl_ref = y["bibl"]
        except (KeyError, TypeError):
            continue
        book = get_book_from_bibl_ref(bibl_ref)["order"]
        ai_refs_old[key].append(book)
save_json(ai_refs_old, "ai_refs_old.json")


source_data = load_json(os.path.join(OUT_DIR, "all_in_one.json"))

ai_refs = defaultdict(list)
for key, value in source_data.items():
    for y in value:
        try:
            bibl_ref = y["bibl"]
        except (KeyError, TypeError):
            continue
        book = get_book_from_bibl_ref(bibl_ref)["order"]
        ai_refs[key].append(book)
save_json(ai_refs, "ai_refs.json")

data = {}
for key, value in ai_refs.items():
    index_id = int(key.split("__")[-1])
    data[index_id] = {"jad_id": key, "ai": sorted(value), "nr_ai": len(value)}
    try:
        data[index_id]["ai_old"] = sorted(ai_refs_old[key])
    except KeyError:
        data[index_id]["ai_old"] = []
    data[index_id]["nr_ai_old"] = len(data[index_id]["ai_old"])


df = pd.DataFrame.from_dict(data, orient="index").sort_index()
df = df[df["nr_ai_old"] > 0]
df["nr_match"] = df["nr_ai"] == df["nr_ai_old"]
df["full_match"] = df.apply(lambda row: row["ai"] == row["ai_old"], axis=1)
df["partial_match"] = df.apply(
    lambda row: bool(set(row["ai"]) & set(row["ai_old"])), axis=1
)
df["all_found"] = df.apply(
    lambda row: set(row["ai_old"]).issubset(set(row["ai"])), axis=1
)
total_rows = len(df)
stats = {
    "partial_match": df["partial_match"].sum(),
    "all_found": df["all_found"].sum(),
    "nr_match": df["nr_match"].sum(),
    "full_match": df["full_match"].sum(),
}
print("\n\n### Books ###\n")
for col, val in stats.items():
    print(f"{col}: {val} out of {total_rows} rows ({val/total_rows*100:.1f}%)")


print("\n\n### Chapters ###\n")
print("Todo: Implement chapter statistics")
