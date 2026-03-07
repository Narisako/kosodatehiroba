import csv
import json
import html

# Read CSV
rows = []
with open('/home/exedev/kosodate_kyoten_all.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append({
            'pref': row.get('pref', row.get('都道府県', '')),
            'city': row.get('city', row.get('自治体名', '')),
            'name': row.get('name', row.get('拠点名', '')),
            'zip': row.get('zip', ''),
            'addr': row.get('addr', row.get('住所', '')),
            'phone': row.get('phone', row.get('電話番号', '')),
            'note': row.get('note', row.get('備考', ''))
        })

# Create JSON data
json_data = json.dumps(rows, ensure_ascii=False)

# Count by prefecture
pref_counts = {}
for r in rows:
    pref_counts[r['pref']] = pref_counts.get(r['pref'], 0) + 1

with open('/home/exedev/kosodate_kyoten_all.json', 'w', encoding='utf-8') as f:
    f.write(json_data)

print(f"JSON created: {len(rows)} rows, {len(json_data)} bytes")

# Generate about.html from README
try:
    import markdown
    with open('/home/exedev/data/csv_by_pref/README.md', 'r') as f:
        md = f.read()
    html = markdown.markdown(md, extensions=['tables', 'fenced_code'])
    with open('/home/exedev/about.html', 'w') as f:
        f.write(html)
    print(f"about.html created: {len(html)} bytes")
except ImportError:
    print("Warning: markdown module not found, skipping about.html")
