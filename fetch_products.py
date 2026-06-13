#!/usr/bin/env python3
"""Trage produsele reale din Store API-ul WooCommerce al yzzy.ro
si genereaza products.js cu catalogul pe categorii pentru demo.
Ruleaza oricand vrei sa actualizezi preturile: python3 fetch_products.py
"""
import json
import re
import urllib.request

BASE = "https://yzzy.ro/wp-json/wc/store/v1/products"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

# cheie demo -> (id categorie WooCommerce, cate produse)
CATEGORIES = {
    "noutati": (None, 8),
    "telefoane": (19, 12),
    "laptopuri": (20, 8),
    "smartwatch": (135, 8),
    "accesorii": (22, 8),
    "tablete": (96, 8),
}

CONDITIONS = ["nou sigilat", "nou desigilat", "ca nou", "excelent", "foarte bun", "bun"]


def strip_tags(html):
    return re.sub(r"<[^>]+>", "", html or "").strip()


def clean(p, default_cond):
    name = p["name"]
    cond = next((c for c in CONDITIONS if c in name.lower()), None)
    short = re.sub(r"^(APPLE|SAMSUNG|HUAWEI|XIAOMI|GOOGLE|LENOVO|ASUS|HP|DELL)\s+", "", name, flags=re.I)
    if cond:
        short = re.sub(re.escape(cond) + r".*$", "", short, flags=re.I)
    short = re.sub(r"\s+YZZY\s*$", "", short, flags=re.I).strip(" ,-")
    if len(short) > 42:
        short = short[:42].rsplit(" ", 1)[0].rstrip(" ,-") + "…"
    img = p["images"][0] if p["images"] else None
    desc = strip_tags(p.get("short_description") or "")
    if len(desc) > 150:
        desc = desc[:150].rsplit(" ", 1)[0] + "…"
    return {
        "name": short,
        "condition": (cond or default_cond).capitalize(),
        "prices": {k: p["prices"][k] for k in ("price", "regular_price", "sale_price", "currency_minor_unit")},
        "on_sale": p["on_sale"],
        "image": img["thumbnail"] if img and img.get("thumbnail") else (img["src"] if img else None),
        "image_full": img["src"] if img else None,
        "url": p["permalink"],
        "desc": desc,
    }


def fetch(cat_id, count):
    url = f"{BASE}?per_page={min(count * 3, 48)}&orderby=date&order=desc"
    if cat_id:
        url += f"&category={cat_id}"
    req = urllib.request.Request(url, headers=UA)
    raw = json.load(urllib.request.urlopen(req))
    default_cond = "nou" if cat_id == 22 else "verificat"
    seen, out = set(), []
    for p in raw:
        c = clean(p, default_cond)
        model = re.sub(r"\d+GB.*$", "", c["name"]).strip()
        if not c["image"] or (model in seen and cat_id is None):
            continue
        seen.add(model)
        out.append(c)
        if len(out) == count:
            break
    return out


catalog = {}
for key, (cat_id, count) in CATEGORIES.items():
    catalog[key] = fetch(cat_id, count)
    print(f"{key}: {len(catalog[key])} produse")

with open("products.js", "w", encoding="utf-8") as f:
    f.write("// generat de fetch_products.py — date reale din yzzy.ro Store API\n")
    f.write("window.YZZY_CATALOG = ")
    json.dump(catalog, f, ensure_ascii=False)
    f.write(";\nwindow.YZZY_PRODUCTS = window.YZZY_CATALOG.noutati;\n")

print("OK — products.js scris")
