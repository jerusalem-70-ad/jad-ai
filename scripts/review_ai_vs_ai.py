import os
import pandas as pd
from config import OUT_DIR
from acdh_bible_pyutils import normalize_bible_refs
from csae_pyutils import load_json

# Load old AI predictions
source_data = load_json(os.path.join(OUT_DIR, "all_in_one_backup.json"))

ai_refs_old = list()
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
    ai_refs_old.append(item)

# Load new AI predictions
source_data = load_json(os.path.join(OUT_DIR, "all_in_one.json"))

ai_refs_new = list()
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
    ai_refs_new.append(item)

# Create dataframes and merge
df_old = pd.DataFrame(ai_refs_old).sort_values("id")
df_old = df_old.drop_duplicates(subset=["jad_id"], keep="first")

df_new = pd.DataFrame(ai_refs_new).sort_values("id")
df_new = df_new.drop_duplicates(subset=["jad_id"], keep="first")

df = df_old.merge(df_new, on="jad_id", how="left", suffixes=("_old", "_new"))
df = df.drop(columns=["id_new"])

# Fill NaN values with empty lists for columns ending with "_new"
new_columns = [col for col in df.columns if col.endswith("_new")]
for col in new_columns:
    df[col] = df[col].apply(lambda x: [] if isinstance(x, float) and pd.isna(x) else x)

# Calculate matches
df["full_match_book"] = df.apply(
    lambda row: row["books_new"] == row["books_old"], axis=1
)
df["full_match_chapter"] = df.apply(
    lambda row: row["chapters_new"] == row["chapters_old"], axis=1
)
df["full_match_verse"] = df.apply(
    lambda row: row["verses_new"] == row["verses_old"], axis=1
)

df["partial_match_book"] = df.apply(
    lambda row: bool(set(row["books_new"]) & set(row["books_old"])), axis=1
)
df["partial_match_chapter"] = df.apply(
    lambda row: bool(set(row["chapters_new"]) & set(row["chapters_old"])), axis=1
)
df["partial_match_verse"] = df.apply(
    lambda row: bool(set(row["verses_new"]) & set(row["verses_old"])), axis=1
)

df["all_found_books"] = df.apply(
    lambda row: set(row["books_old"]).issubset(set(row["books_new"])), axis=1
)
df["all_found_chapters"] = df.apply(
    lambda row: set(row["chapters_old"]).issubset(set(row["chapters_new"])), axis=1
)
df["all_found_verses"] = df.apply(
    lambda row: set(row["verses_old"]).issubset(set(row["verses_new"])), axis=1
)

# Calculate and print statistics
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

print("\n### AI vs AI Comparison ###\n")
for col, val in stats.items():
    print(
        f"{col.replace('_', ' ').title()}: {val} out of {total_rows} passages ({val/total_rows*100:.1f}%)"
    )

print("\n### Done ###\n")
df.to_csv(os.path.join(OUT_DIR, "ai_vs_ai.csv"), index=False)
