import os
import json
import requests
from acdh_baserow_pyutils import BaseRowClient
from config import PASSAGES_URL

print("foo")
with open(os.path.join("out", "all_in_one.json"), "r", encoding="utf-8") as fp:
    data = json.load(fp)
print(f"loading passages from {PASSAGES_URL}")
passages = requests.get(PASSAGES_URL).json()
ids = [int(x) for x in passages.keys()]
print("done loading")
payload = []
for key, value in data.items():
    item = {}
    item["id"] = int(key.split("__")[-1])
    if item["id"] not in ids:
        print(f"{item['id']} does not exist any more")
        continue
    try:
        item["ai_bible_refs"] = "; ".join(set([x["bibl"] for x in value]))
    except TypeError:
        continue
    payload.append(item)

BASEROW_DB_ID = 578
BASEROW_URL = "https://baserow.acdh-dev.oeaw.ac.at/api/"
BASEROW_USER = os.environ.get("BASEROW_USER")
BASEROW_PW = os.environ.get("BASEROW_PW")
BASEROW_TOKEN = os.environ.get("BASEROW_TOKEN")


try:
    br_client = BaseRowClient(
        BASEROW_USER, BASEROW_PW, BASEROW_TOKEN, br_base_url=BASEROW_URL, br_db_id=BASEROW_DB_ID
    )
except KeyError:
    br_client = None

updated = br_client.batch_update_rows(3500, payload)
if updated["errors"]:
    for x in updated["errors"]:
        print(x)
else:
    print("no errors, good job!")
print("done")
