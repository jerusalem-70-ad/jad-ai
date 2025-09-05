import os
import json
import requests
from openai import OpenAI

from config import KEYWORD_URL, SUMMARIES_DIR, PASSAGES_URL

os.makedirs(SUMMARIES_DIR, exist_ok=True)

source_data = requests.get(KEYWORD_URL).json()
keywords = [value["name"] for _, value in source_data.items()]

source_data = requests.get(PASSAGES_URL).json()

data = [
    {"jad_id": value["jad_id"], "passage": value["passage"], "text_paragraph": value["text_paragraph"]}
    for _, value in source_data.items()
]

prompt = """
Please provide an english summary for thi text({}). Also one to three keywords that best describe the text. The keywords shoudl be taken from the following list: {}. The result should ba JSON with a key "summary", the value should be a string and a key "keywords" should be a list of strings. If the text is too long, please summarize the text to the best of your ability.
"""  # noqa: E501

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
for x in data:
    json_file_path = os.path.join(SUMMARIES_DIR, f"{x['jad_id']}.json")
    if x["text_paragraph"]:
        text_to_process = x["text_paragraph"]
    elif x["passage"]:
        text_to_process = x["passage"]
        if os.path.exists(json_file_path):
            continue
        else:
            print(f"processing {x['jad_id']}")
            try:
                completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": prompt.format(text_to_process, ", ".join(keywords)),
                        }
                    ],
                    model="gpt-4o",
                )
                result = completion.choices[0].message.content
                json_result = result.replace("```json\n", "").replace("```", "")
            except Exception as e:
                print(f"failed to process {x['jad_id']} due to {e}")
            try:
                data = json.loads(json_result)
            except:  # noqa
                print(f"no proper json returned for {x['jad_id']}")
                data = {"summary": "", "keywords": []}
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    else:
        print(f"Skipping {x['jad_id']} because it has no text.")

print("Done")
