import http.client, json

conn = http.client.HTTPConnection('127.0.0.1', 8000)
boundary = 'BOUNDARY123'

with open('dataset/tampered/tampered_date_altered.jpg', 'rb') as f:
    data = f.read()

body = (
    b'--BOUNDARY123\r\n'
    b'Content-Disposition: form-data; name="file"; filename="tampered_date_altered.jpg"\r\n'
    b'Content-Type: image/jpeg\r\n\r\n' +
    data +
    b'\r\n--BOUNDARY123--\r\n'
)

headers = {
    'Content-Type': 'multipart/form-data; boundary=BOUNDARY123',
    'Content-Length': str(len(body))
}

conn.request('POST', '/analyze', body=body, headers=headers)
resp = conn.getresponse()
result = json.loads(resp.read())

print('=== ANALYSIS RESULT ===')
print('Authenticity Index:', result['authenticity_index'], '%')
print('Risk Index:', result['risk_index'], '%')
print('Integrity Label:', result['integrity_label'])
print('Modules Flagged:', result['modules_flagged'], '/6')
print('Total Anomalies:', result['total_anomalies'])
print()
print('=== TEST CASES ===')
for tc in result.get('test_cases', []):
    print(f"  [{tc['id'].upper()}] {tc['name']}")
    print(f"    Score: {tc['score_pct']}% | Risk: {tc['risk_level']} | Flagged: {tc['flagged']}")
    print(f"    Verdict: {tc['verdict']}")
