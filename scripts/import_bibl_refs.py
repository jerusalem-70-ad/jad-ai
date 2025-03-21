import os
import glob
import json
from collections import defaultdict
from tqdm import tqdm
from acdh_baserow_pyutils import BaseRowClient

files = glob.glob("./data/*.json")

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

table_dict = br_client.br_table_dict

d = defaultdict(set)
for x in files:
    occ_id = os.path.split(x)[1].replace(".json", "")
    with open(x, "r", encoding="utf-8") as fp:
        data = json.load(fp)
        for item in data:
            try:
                bibl = f'{item["bibl"]} (AI)'
            except:  # noqa:
                continue
            d[bibl].add(occ_id)

for key, value in tqdm(d.items(), total=len(d)):
    patch_item = {}
    obj = br_client.get_or_create("ai_bibl_ref", "name", table_dict, key)[0]
    obj_id = str(obj["id"])
    patch_item["occurrences"] = [int(x.split("__")[-1]) for x in value]
    patched = br_client.patch_row("4160", obj_id, patch_item)
