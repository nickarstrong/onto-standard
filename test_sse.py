import requests, json, threading

GOLD = ''
ready = threading.Event()

def sse_listener():
    global GOLD
    r = requests.get('https://api.ontostandard.org/v1/gold/stream', headers={'x-api-key': 'onto_fcd4fbf5e7f1fd3a76dd2c01c7515d13c3599ac4975d2517'}, stream=True, timeout=60)
    for line in r.iter_lines():
        if not line: continue
        data = json.loads(line.decode().removeprefix('data: '))
        if data['type'] in ('gold_corpus', 'gold_update'):
            GOLD = data['discipline_layer']
            ready.set()
            return

threading.Thread(target=sse_listener, daemon=True).start()
ready.wait(timeout=15)
print('GOLD:', len(GOLD), 'chars')

r2 = requests.post(
    'https://api.anthropic.com/v1/messages',
    headers={
        'x-api-key': 'sk-ant-api03-nPqVRvunphhjiLWfNvAe-jb9Y0xqPcVe27qe3eKiaY3JiLQ64FlHsLZ1HfTQ5VVZCo1p42irpzfwZnItKJ3bNuOyw-w80ctAAA',
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json'
    },
    json={
        'model': 'claude-sonnet-4-20250514',
        'max_tokens': 512,
        'system': GOLD,
        'messages': [{'role': 'user', 'content': 'What is the boiling point of water?'}]
    }
)
print('Status:', r2.status_code)
data = r2.json()
err = data.get('error')
if err:
    print('Error:', err)
else:
    response = ''.join(c.get('text','') for c in data.get('content',[]))
    print('Response:', len(response), 'chars')
    print(response[:500])
