import requests

token = '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'
headers = {'Authorization': f'token {token}', 'User-Agent': 'OpenSeismoLite'}
try:
    r = requests.get('https://api.github.com/user', headers=headers, timeout=10)
    print('status', r.status_code)
    try:
        j = r.json()
        print('login', j.get('login'))
        print('id', j.get('id'))
        print('name', j.get('name'))
    except Exception as e:
        print('json_error', e)
        print(r.text)
except Exception as e:
    print('error', e)
