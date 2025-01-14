import os
import requests
from openai import OpenAI
import json


URL = "https://raw.githubusercontent.com/jerusalem-70-ad/jad-baserow-dump/refs/heads/main/json_dumps/occurrences.json"  # noqa: E501
DATA_DIR = "data"

source_data = requests.get(URL).json()

data = [
    {"jad_id": value["jad_id"], "text_paragraph": value["text_paragraph"]}
    for key, value in source_data.items()
]


prompt = """please find all biblical references in this text ({}) and return the result as json. The JSON should have keys: 'bibl' and 'text'. Each reference should its own object. All values should be strings. If there are no biblical references, please return an empty list. Please note that the text may contain multiple biblical references. Please also note that the text may contain multiple sentences."""  # noqa: E501

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
for x in data:
    if x["text_paragraph"]:
        print(f"processing {x['jad_id']}")
        json_file_path = os.path.join(DATA_DIR, f"{x['jad_id']}.json")
        if os.path.exists(json_file_path):
            print(f"File {json_file_path} already exists. Skipping.")
            continue
        else:
            completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": prompt.format(x["text_paragraph"]),
                    }
                ],
                model="gpt-4o",
            )
            result = completion.choices[0].message.content
            json_result = result.replace("```json\n", "").replace("```", "")
            try:
                data = json.loads(json_result)
                json_good = True
            except Exception as e:
                print(e)
                json_good = False
            with open(
                json_file_path.replace(".json", "text"), "w", encoding="utf-8"
            ) as f:
                f.write(json_result)
            if json_good:
                with open(json_file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
    else:
        print(f"Skipping {x['jad_id']} because it has no text.")

print("Done")
