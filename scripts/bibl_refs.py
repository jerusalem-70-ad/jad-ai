import os
import requests
from openai import OpenAI
import json

from config import PASSAGES_URL, DATA_DIR


URL = PASSAGES_URL
source_data = requests.get(URL).json()

os.makedirs(DATA_DIR, exist_ok=True)

data = [
    {"jad_id": value["jad_id"], "text_paragraph": value["text_paragraph"]}
    for key, value in source_data.items()
]


prompt = """please find all biblical references in this text ({}) and return the result as json. The JSON should have keys: 'bibl' and 'text'. Each reference should its own object. All values should be strings. If there are no biblical references, please return an empty list. Please note that the text may contain multiple biblical references. Please also note that the text may contain multiple sentences. Don't use latin numbers for bibl but something like Matthew 27:50-52"""  # noqa: E501

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
for x in data:
    jad_id = x["jad_id"]
    if x["text_paragraph"]:
        json_file_path = os.path.join(DATA_DIR, f"{jad_id}.json")
        if os.path.exists(json_file_path):
            print(f"File {json_file_path} already exists. Skipping.")
            continue
        else:
            print(f"processing {jad_id}")
            try:
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
            except Exception as e:
                print(f"failed to process {jad_id} because of {e}")
                json_results = "[]"
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
        print(f"Skipping {jad_id} because it has no text.")

print("Done")
