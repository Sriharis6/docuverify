import http.client, json

def analyze(fpath, fname):
    conn = http.client.HTTPConnection('127.0.0.1', 8000)
    with open(fpath, 'rb') as f:
        data = f.read()
    disp = ('Content-Disposition: form-data; name="file"; filename="' + fname + '"').encode()
    body = (
        b'--BOUND7777\r\n' +
        disp + b'\r\n'
        b'Content-Type: image/jpeg\r\n\r\n' +
        data +
        b'\r\n--BOUND7777--\r\n'
    )
    headers = {
        'Content-Type': 'multipart/form-data; boundary=BOUND7777',
        'Content-Length': str(len(body))
    }
    conn.request('POST', '/analyze', body=body, headers=headers)
    resp = conn.getresponse()
    return json.loads(resp.read())

docs = [
    ('dataset/genuine/genuine_certificate.jpg',      'genuine_certificate.jpg',    'Genuine Certificate'),
    ('dataset/genuine/genuine_id_card.jpg',           'genuine_id_card.jpg',        'Genuine ID Card'),
    ('dataset/tampered/tampered_date_altered.jpg',    'tampered_date_altered.jpg',  'Tampered — Date Altered'),
    ('dataset/tampered/tampered_copy_move.jpg',       'tampered_copy_move.jpg',     'Tampered — Copy-Move'),
    ('dataset/tampered/tampered_ela_artifact.jpg',    'tampered_ela_artifact.jpg',  'Tampered — ELA Artifact'),
]

for fpath, fname, label in docs:
    print('=' * 60)
    print('DOC:', label)
    print('=' * 60)
    try:
        r = analyze(fpath, fname)
        print('  Integrity  :', r['authenticity_index'], '%')
        print('  Label      :', r['integrity_label'])
        print('  Risk Index :', r['risk_index'], '%')
        print('  Mod Flagged:', str(r['modules_flagged']) + '/6')
        print()
        for tc in r['test_cases']:
            flag = '[FLAGGED]' if tc['flagged'] else '         '
            print(f"  {flag}  {tc['name']:<32}  {tc['score_pct']:5.1f}%  [{tc['risk_level']}]")
            print(f"           Verdict: {tc['verdict']}")
        print()
    except Exception as e:
        print('  ERROR:', e)
    print()
