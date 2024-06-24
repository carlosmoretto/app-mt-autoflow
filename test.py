from backend.fintera_financeiro_api.helper import helper
import pandas as pd
import json
from pandas import json_normalize
#hp = helper().get_entities()


with open('response.json', 'r', encoding='utf-8') as file:
    data = json.load(file)


df = json_normalize(data, meta=["id", "entity_id", "download_url", "attachables.type"])