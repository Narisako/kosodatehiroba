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
