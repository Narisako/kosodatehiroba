# kosodatehiroba

地域子育て支援拠点データを都道府県別CSVで管理するリポジトリです。

## データファイル

- 全体CSV: `kosodate_kyoten_all.csv`
- 全体JSON: `kosodate_kyoten_all.json`
- 都道府県別CSV: `data/csv_by_pref/*.csv`

## 進捗・カバレッジ

都道府県別の件数、欠損市町村、データソースは以下を参照してください。

- `data/csv_by_pref/README.md`

## 形式

都道府県別CSVのカラム:

`pref, city, name, addr, phone, note`

（UTF-8 BOM付き）
