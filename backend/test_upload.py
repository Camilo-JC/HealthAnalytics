import urllib.request, json, tempfile, os

login_data = json.dumps({'email': 'admin@healthcare-etl.com', 'password': 'Admin123!'}).encode()
req = urllib.request.Request('http://127.0.0.1:8000/api/v1/auth/login/', data=login_data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req)
login = json.loads(resp.read())
token = login['access']
print('Token OK')

csv = b'name,age,gender\nJohn,30,M\nJane,25,F\nBob,45,M'
boundary = '----TestBoundary12345'
lines = []
lines.append('--' + boundary)
lines.append('Content-Disposition: form-data; name="name"')
lines.append('')
lines.append('test_upload.csv')
lines.append('--' + boundary)
lines.append('Content-Disposition: form-data; name="source_type"')
lines.append('')
lines.append('csv')
lines.append('--' + boundary)
lines.append('Content-Disposition: form-data; name="file"; filename="test_upload.csv"')
lines.append('Content-Type: text/csv')
lines.append('')
lines.append(csv.decode())
lines.append('--' + boundary + '--')
body_data = '\r\n'.join(lines).encode()

req = urllib.request.Request('http://127.0.0.1:8000/api/v1/etl/sources/', data=body_data, headers={
    'Content-Type': 'multipart/form-data; boundary=' + boundary,
    'Authorization': 'Bearer ' + token,
})
try:
    resp = urllib.request.urlopen(req)
    print('Status:', resp.status)
    print('Body:', resp.read().decode()[:500])
except urllib.error.HTTPError as e:
    print('Status:', e.code)
    print('Body:', e.read().decode()[:2000])
