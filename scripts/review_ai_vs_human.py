import requests
import os
import pandas as pd
from config import PASSAGES_URL, OUT_DIR
from acdh_bible_pyutils import normalize_bible_refs
from csae_pyutils import save_json, load_json

print("`$ python review_ai_vs_human.py`")


URL = PASSAGES_URL
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
    "longest_passage": df.loc[df["word_count"].idxmax()]["id"],
    "shortest_passage": df.loc[df["word_count"].idxmin()]["id"],
    "longest_passage_word_count": int(df["word_count"].max()),
    "shortest_passage_word_count": int(df["word_count"].min()),
}
print("\n### Passages and words ###\n")
for key, value in stats.items():
    print(f"{key.replace('_', ' ').title()}: {value}")

manual_refs = list()
for x in source_data.values():
    # we need to remove passages without text paragraphs because
    # there are passages without texts but with biblical references
    if x["text_paragraph"]:
        bibl_refs = x["biblical_references"]
        jad_id = x["jad_id"]
        num = int(jad_id.split("__")[-1])
        if bibl_refs:
            item = {
                "id": num,
                "jad_id": jad_id,
                "books": [],
                "chapters": [],
                "verses": [],
            }
            for y in bibl_refs:
                books = item["books"]
                chapters = item["chapters"]
                verses = item["verses"]
                normalized_ref = normalize_bible_refs(y["value"])
                books.append(normalized_ref["order"])
                chapters.append(normalized_ref["chapter"])
                verse_string = f'{normalized_ref["title_lat"]} {normalized_ref["chapter"]}:{normalized_ref["verse_start"]}'  # noqa: E501
                verses.append(verse_string)
        manual_refs.append(item)
save_json(manual_refs, "manual_refs.json")

source_data = load_json(os.path.join(OUT_DIR, "all_in_one.json"))

ai_refs = list()
for key, value in source_data.items():
    jad_id = key
    num = int(jad_id.split("__")[-1])
    item = {
        "id": num,
        "jad_id": jad_id,
        "books": [],
        "chapters": [],
        "verses": [],
    }
    for y in value:
        try:
            bibl_ref = y["bibl"]
        except (KeyError, TypeError):
            continue
        books = item["books"]
        chapters = item["chapters"]
        verses = item["verses"]
        normalized_ref = normalize_bible_refs(y["bibl"])
        books.append(normalized_ref["order"])
        chapters.append(normalized_ref["chapter"])
        verse_string = f'{normalized_ref["title_lat"]} {normalized_ref["chapter"]}:{normalized_ref["verse_start"]}'
        verses.append(verse_string)
    for key, value in item.items():
        if isinstance(value, list):
            item[key] = sorted(value)
    ai_refs.append(item)
save_json(ai_refs, "ai_refs.json")

df_manual = pd.DataFrame(manual_refs).sort_values("id")
df_manual = df_manual.drop_duplicates(subset=["jad_id"], keep="first")

df_ai = pd.DataFrame(ai_refs).sort_values("id")
df_ai = df_ai.drop_duplicates(subset=["jad_id"], keep="first")
df = df_manual.merge(df_ai, on="jad_id", how="left", suffixes=("_manual", "_ai"))
df = df.drop(columns=["id_ai"])
# Fill NaN values with empty lists for columns ending with "_ai"
ai_columns = [col for col in df.columns if col.endswith("_ai")]
for col in ai_columns:
    df[col] = df[col].apply(lambda x: [] if isinstance(x, float) and pd.isna(x) else x)

df["full_match_book"] = df.apply(
    lambda row: row["books_ai"] == row["books_manual"], axis=1
)
df["full_match_chapter"] = df.apply(
    lambda row: row["chapters_ai"] == row["chapters_manual"], axis=1
)
df["full_match_verse"] = df.apply(
    lambda row: row["verses_ai"] == row["verses_manual"], axis=1
)

df["partial_match_book"] = df.apply(
    lambda row: bool(set(row["books_ai"]) & set(row["books_manual"])), axis=1
)
df["partial_match_chapter"] = df.apply(
    lambda row: bool(set(row["chapters_ai"]) & set(row["chapters_manual"])), axis=1
)
df["partial_match_verse"] = df.apply(
    lambda row: bool(set(row["verses_ai"]) & set(row["verses_manual"])), axis=1
)
df["all_found_books"] = df.apply(
    lambda row: set(row["books_manual"]).issubset(set(row["books_ai"])), axis=1
)
df["all_found_chapters"] = df.apply(
    lambda row: set(row["chapters_manual"]).issubset(set(row["chapters_ai"])), axis=1
)
df["all_found_verses"] = df.apply(
    lambda row: set(row["verses_manual"]).issubset(set(row["verses_ai"])), axis=1
)

total_rows = len(df)
stats = {
    "partial_match_book": df["partial_match_book"].sum(),
    "partial_match_chapter": df["partial_match_chapter"].sum(),
    "partial_match_verse": df["partial_match_verse"].sum(),
    "all_found_books": df["all_found_books"].sum(),
    "all_found_chapters": df["all_found_chapters"].sum(),
    "all_found_verses": df["all_found_verses"].sum(),
    "full_match_book": df["full_match_book"].sum(),
    "full_match_chapter": df["full_match_chapter"].sum(),
    "full_match_verse": df["full_match_verse"].sum(),
}
print("\n### Human vs AI ###\n")
for col, val in stats.items():
    print(
        f"{col.replace('_', ' ').title()}: {val} out of {total_rows} passages ({val/total_rows*100:.1f}%)"
    )

print("\n### Done ###\n\n")
df.to_csv(os.path.join(OUT_DIR, "human_vs_ai.csv"), index=False)
