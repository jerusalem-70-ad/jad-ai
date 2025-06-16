import requests
import pandas as pd
from config import PASSAGES_URL


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

for key, value in stats.items():
    print(f"{key.replace('_', ' ').title()}: {value}")
