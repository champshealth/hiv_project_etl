import requests, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config.config import REDCAP_31_TOKENS, REDCAP_URL

t = str(REDCAP_31_TOKENS[0]['token'])
for ps in [500, 1000, 5000]:
    d = {'token': t, 'content': 'record', 'action': 'export', 'format': 'json', 'type': 'flat', 'page': 1, 'pageSize': ps}
    r = requests.post(REDCAP_URL, data=d, timeout=30)
    data = r.json()
    print(f'pageSize={ps}: page 1 has {len(data)} records')
    if len(data) > 0:
        print(f'  columns: {len(data[0].keys())}')
