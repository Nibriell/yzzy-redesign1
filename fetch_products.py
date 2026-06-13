#!/usr/bin/env python3
"""Trage produsele reale din Store API-ul WooCommerce al yzzy.ro
si genereaza products.js cu datele necesare cardurilor din demo.
Ruleaza oricand vrei sa actualizezi preturile: python3 fetch_products.py
"""
import json
import re
import urllib.request

API = "https://yzzy.ro/wp-json/wc/store/v1/products?per_page=24&orderby=date&order=desc"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

CONDITIONS = ["nou sigilat", "nou desigilat", "ca nou", "excelent", "foarte bun", "bun"]

def clean(p):
    name = p["name"]
    cond = next((c for c in CONDITIONS if c in name.lower()), None)
    short = re.sub(r"^(APPLE|SAMSUNG)\s+", "", name, flags=re.I)
    if cond:
        short = re.sub(re.escape(cond) + r".*$", "", short, flags=re.I)
    short = re.sub(r"\s+YZZY\s*$", "", short, flags=re.I).strip(" ,-")
    if len(short) > 42:
        short = short[:42].rsplit(" ", 1)[0].rstrip(" ,-") + "…"
    return {
        "name": short,
        "condition": (cond or "verificat").capitalize(),
        "prices": p["prices"],
        "on_sale": p["on_sale"],
        "image": p["images"][0]["thumbnail" if p["images"][0].get("thumbnail") else "src"] if p["images"] else None,
        "url": p["permalink"],
    }

req = urllib.request.Request(API, headers=UA)
products = json.load(urllib.request.urlopen(req))

seen, picked = set(), []
for p in products:
    c = clean(p)
    model = re.sub(r"\d+GB.*$", "", c["name"]).strip()
    if model in seen or not c["image"]:
        continue
    seen.add(model)
    picked.append(c)
    if len(picked) == 8:
        break

with open("products.js", "w", encoding="utf-8") as f:
    f.write("// generat de fetch_products.py — date reale din yzzy.ro Store API\n")
    f.write("window.YZZY_PRODUCTS = ")
    json.dump(picked, f, ensure_ascii=False, indent=1)
    f.write(";\n")

print(f"OK — {len(picked)} produse scrise in products.js")
for c in picked:
    print(" -", c["name"], "|", c["condition"], "|", int(c["prices"]["price"]) / 100, "lei")
