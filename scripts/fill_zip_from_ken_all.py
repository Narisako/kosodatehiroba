#!/usr/bin/env python3
import csv
import io
import os
import re
import unicodedata
import urllib.request
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "csv_by_pref"
KEN_ALL_ZIP_URL = "https://www.post.japanpost.jp/zipcode/dl/kogaki/zip/ken_all.zip"

HYPHENS = "‐‑‒–—―ーｰ−"
TRANS = str.maketrans({c: "-" for c in HYPHENS})
RE_SPACES = re.compile(r"[\s\u3000]+")
RE_PARENS = re.compile(r"（[^）]*）|\([^\)]*\)")
RE_TRAIL_NUM = re.compile(r"[-0-9０-９一二三四五六七八九十丁目番地号の]+$")


@dataclass
class TownEntry:
    town: str
    zips: set


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.translate(TRANS)
    s = RE_SPACES.sub("", s)
    s = s.replace("ヶ", "ケ")
    return s.strip()


def strip_optional_prefixes(s: str) -> str:
    for p in ("大字", "字"):
        if s.startswith(p):
            return s[len(p) :]
    return s


def clean_addr_for_match(addr: str) -> str:
    a = norm(addr)
    a = a.replace("〒", "")
    a = RE_PARENS.sub("", a)
    return a


def fetch_ken_all() -> io.StringIO:
    with urllib.request.urlopen(KEN_ALL_ZIP_URL, timeout=60) as r:
        z = r.read()
    with zipfile.ZipFile(io.BytesIO(z)) as zf:
        name = [n for n in zf.namelist() if n.upper().endswith("KEN_ALL.CSV")][0]
        raw = zf.read(name)
    txt = raw.decode("cp932", errors="replace")
    return io.StringIO(txt)


def load_ken_all():
    f = fetch_ken_all()
    rd = csv.reader(f)
    muni_to_towns = defaultdict(lambda: defaultdict(set))
    pref_to_munis = defaultdict(set)
    for row in rd:
        if len(row) < 9:
            continue
        zip_code = row[2].strip()
        pref = row[6].strip()
        city = row[7].strip()
        town = row[8].strip()
        if not pref or not city or not zip_code:
            continue
        if "以下に掲載がない場合" in town:
            town = ""
        town = re.sub(r"（.*", "", town)
        key_muni = norm(pref + city)
        key_town = norm(town)
        muni_to_towns[key_muni][key_town].add(zip_code)
        pref_to_munis[norm(pref)].add(key_muni)

    # sort town keys by length desc for prefix match
    muni_sorted = {}
    for muni, town_map in muni_to_towns.items():
        items = []
        for t, z in town_map.items():
            items.append((t, z))
        items.sort(key=lambda x: len(x[0]), reverse=True)
        muni_sorted[muni] = items

    pref_muni_sorted = {}
    for pref, munis in pref_to_munis.items():
        pref_muni_sorted[pref] = sorted(munis, key=len, reverse=True)
    return muni_sorted, pref_muni_sorted


def _resolve_on_address(pref_n: str, city_n: str, a: str, muni_sorted, pref_muni_sorted):
    a_wo_pref = a[len(pref_n) :] if a.startswith(pref_n) else a

    muni_candidates = []
    for muni in pref_muni_sorted.get(pref_n, []):
        muni_no_pref = muni[len(pref_n) :] if muni.startswith(pref_n) else muni
        if a.startswith(muni) or a_wo_pref.startswith(muni_no_pref):
            muni_candidates.append((muni, muni_no_pref))

    # fallback: city-based candidate when county prefix differs
    if not muni_candidates:
        for muni in pref_muni_sorted.get(pref_n, []):
            muni_no_pref = muni[len(pref_n) :] if muni.startswith(pref_n) else muni
            if muni_no_pref.endswith(city_n) and city_n and city_n in a_wo_pref:
                muni_candidates.append((muni, muni_no_pref))

    for muni, muni_no_pref in muni_candidates:
        tail = a_wo_pref
        if tail.startswith(muni_no_pref):
            tail = tail[len(muni_no_pref) :]
        tail2 = strip_optional_prefixes(tail)

        best_len = -1
        best_zips = None
        for town, zips in muni_sorted.get(muni, []):
            if town == "":
                continue
            towns = [town, strip_optional_prefixes(town)]
            for t in towns:
                if t and (tail.startswith(t) or tail2.startswith(t)):
                    tlen = len(t)
                    if tlen > best_len:
                        best_len = tlen
                        best_zips = zips
                    elif tlen == best_len and best_zips is not None:
                        best_zips = set(best_zips) | set(zips)

        if best_zips and len(best_zips) == 1:
            return list(best_zips)[0], None
        if best_zips and len(best_zips) > 1:
            return None, f"ambiguous-town-{len(best_zips)}"

        # fallback to townless entry for this municipality if unique
        for town, zips in muni_sorted.get(muni, []):
            if town == "" and len(zips) == 1:
                return list(zips)[0], None

    return None, "no-deterministic-match"


def resolve_zip(pref: str, city: str, addr: str, muni_sorted, pref_muni_sorted):
    pref_n = norm(pref)
    city_n = norm(city)
    a = clean_addr_for_match(addr)

    variants = [a]
    # many rows omit pref/city in addr; add deterministic variants
    if city_n and city_n not in a:
        variants.append(pref_n + city_n + a)
        variants.append(city_n + a)
    elif pref_n and not a.startswith(pref_n):
        variants.append(pref_n + a)

    seen = set()
    for cand in variants:
        if cand in seen:
            continue
        seen.add(cand)
        z, reason = _resolve_on_address(pref_n, city_n, cand, muni_sorted, pref_muni_sorted)
        if z:
            return z, None
        if reason.startswith("ambiguous"):
            return None, reason

    return None, "no-deterministic-match"


def main():
    muni_sorted, pref_muni_sorted = load_ken_all()

    total_updated = 0
    unresolved = []

    for path in sorted(DATA_DIR.glob("*.csv")):
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            rd = csv.DictReader(f)
            fields = rd.fieldnames
            rows = list(rd)

        changed = False
        for i, row in enumerate(rows, start=2):
            zip_v = (row.get("zip") or "").strip()
            addr = (row.get("addr") or "").strip()
            if zip_v or not addr:
                continue
            z, reason = resolve_zip(row.get("pref", ""), row.get("city", ""), addr, muni_sorted, pref_muni_sorted)
            if z:
                row["zip"] = z
                changed = True
                total_updated += 1
            else:
                unresolved.append((path.name, i, row.get("pref", ""), row.get("city", ""), row.get("name", ""), addr, reason))

        if changed:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                wr = csv.DictWriter(f, fieldnames=fields)
                wr.writeheader()
                wr.writerows(rows)

    unresolved_path = ROOT / "data" / "csv_by_pref" / "zip_unresolved_rows.tsv"
    with open(unresolved_path, "w", encoding="utf-8") as f:
        f.write("file\tline\tpref\tcity\tname\taddr\treason\n")
        for r in unresolved:
            f.write("\t".join(map(str, r)) + "\n")

    print(f"updated={total_updated}")
    print(f"unresolved={len(unresolved)}")
    print(f"unresolved_file={unresolved_path}")


if __name__ == "__main__":
    main()
