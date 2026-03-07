# kosodatehiroba

地域子育て支援拠点データを都道府県別CSVで管理するリポジトリです。

## データファイル

- 全体CSV: `kosodate_kyoten_all.csv`
- 全体JSON: `kosodate_kyoten_all.json`
- 都道府県別CSV: `data/csv_by_pref/*.csv`
- 都道府県別の集約CSV: `data/csv_by_pref/all_prefectures.csv`

## 進捗・カバレッジ

都道府県別の件数、欠損市町村、データソースは以下を参照してください。

- `data/csv_by_pref/README.md`

## 形式

都道府県別CSV / 集約CSV のカラム:

`pref, city, name, zip, addr, phone, note`

- 文字コード: UTF-8（BOM付き）
- `zip` は日本郵便 KEN_ALL ベースで補完済み（未解決は `data/csv_by_pref/zip_unresolved_rows.tsv`）
