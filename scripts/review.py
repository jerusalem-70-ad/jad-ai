from collections import defaultdict
import requests
import os
import pandas as pd
from config import PASSAGES_URL, OUT_DIR
from acdh_bible_pyutils import get_book_from_bibl_ref
from csae_pyutils import save_json, load_json


URL = PASSAGES_URL
APP_URL = "https://jerusalem-70-ad.github.io/jad-astro/passages/"
source_data = requests.get(URL).json()

data = []
for key, value in source_data.items():
    if value["text_paragraph"]:
        item = {"id": value["jad_id"], "text_paragraph": value["text_paragraph"]}
        if value["biblical_references"]:
            item["biblical_references"] = True
        else:
            item["biblical_references"] = False
        data.append(item)

df = pd.DataFrame(data)

df["word_count"] = df["text_paragraph"].apply(lambda x: len(x.split()))

stats = {
    "passages_processed": len(source_data),
    "total_passages": len(df),
    "total_words": int(df["word_count"].sum()),
    "average_words_per_passage": float(df["word_count"].mean()),
    "25th_percentile_words": int(df["word_count"].quantile(0.25)),
    "50th_percentile_words": int(df["word_count"].quantile(0.50)),
    "75th_percentile_words": int(df["word_count"].quantile(0.75)),
    "max_words_in_passage": int(df["word_count"].max()),
    "min_words_in_passage": int(df["word_count"].min()),
    "passages_with_biblical_references": int(df["biblical_references"].sum()),
    "passages_without_biblical_references": int(
        len(df) - df["biblical_references"].sum()
    ),
    "longest_passage": f'{APP_URL}{df.loc[df["word_count"].idxmax()]["id"]}',
    "shortest_passage": f'{APP_URL}{df.loc[df["word_count"].idxmin()]["id"]}',
    "longest_passage_word_count": int(df["word_count"].max()),
    "shortest_passage_word_count": int(df["word_count"].min()),
}
print("\n\n### Passages and words ###\n")
for key, value in stats.items():
    print(f"{key.replace('_', ' ').title()}: {value}")


URL = PASSAGES_URL
APP_URL = "https://jerusalem-70-ad.github.io/jad-astro/passages/"
source_data = requests.get(URL).json()

manual_refs = defaultdict(list)
for x in source_data.values():
    bibl_refs = x["biblical_references"]
    if bibl_refs:
        for y in bibl_refs:
            book_name = get_book_from_bibl_ref(y["value"])["order"]
            manual_refs[x["jad_id"]].append(book_name)
save_json(manual_refs, "manual_refs.json")

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
        data[index_id]["manual"] = sorted(manual_refs[key])
    except KeyError:
        data[index_id]["manual"] = []
    data[index_id]["nr_manual"] = len(data[index_id]["manual"])


df = pd.DataFrame.from_dict(data, orient="index").sort_index()
df = df[df["nr_manual"] > 0]
df["nr_match"] = df["nr_ai"] == df["nr_manual"]
df["full_match"] = df.apply(lambda row: row["ai"] == row["manual"], axis=1)
df["partial_match"] = df.apply(
    lambda row: bool(set(row["ai"]) & set(row["manual"])), axis=1
)
df["all_found"] = df.apply(
    lambda row: set(row["manual"]).issubset(set(row["ai"])), axis=1
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
