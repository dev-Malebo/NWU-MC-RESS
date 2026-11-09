#!/usr/bin/env python3
"""
FREE way to get exact driving distance (km) from NWU Mahikeng Campus
to each residence — no Google API key required.

Uses:
  - Photon (Komoot) free geocoder  OR  Nominatim (slower, stricter limits)
  - OSRM public routing server (OpenStreetMap)

How to run (on your laptop):
  1. pip install requests
  2. Export addresses from the site into addresses.csv:
        name,address
        MAK Accommodations,"34 Dan Pienaar Street, Golfview, Mahikeng"
  3. python get_distances_free.py
  4. Results → distances.csv  (name, address, km, minutes)

Notes:
  - Public OSRM is free but rate-limited. Script waits between requests.
  - Some informal streets in Mmabatho may not geocode; those stay blank.
  - For those, use the site's "Get Directions" button (always exact on Google Maps).
  - Better accuracy: sign up free at https://openrouteservice.org (2 000 req/day).
"""

import csv
import time
import urllib.parse
import urllib.request
import json
import sys

# NWU Mahikeng Campus (official-ish GPS)
CAMPUS_LON = 25.608889
CAMPUS_LAT = -25.828889

INPUT = "addresses.csv"   # columns: name,address
OUTPUT = "distances.csv"
DELAY = 1.2               # seconds between requests (be polite)


def geocode_photon(query: str):
    q = urllib.parse.quote(query + ", South Africa")
    url = f"https://photon.komoot.io/api/?q={q}&limit=1&lang=en"
    req = urllib.request.Request(url, headers={"User-Agent": "NWU-Student-Residences/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode())
    feats = data.get("features") or []
    if not feats:
        return None
    lon, lat = feats[0]["geometry"]["coordinates"]
    return float(lon), float(lat)


def route_osrm(lon1, lat1, lon2, lat2):
    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}?overview=false"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "NWU-Student-Residences/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode())
    if data.get("code") != "Ok":
        return None, None
    route = data["routes"][0]
    km = round(route["distance"] / 1000, 1)
    minutes = round(route["duration"] / 60)
    return km, minutes


def main():
    try:
        rows = list(csv.DictReader(open(INPUT, encoding="utf-8")))
    except FileNotFoundError:
        print(f"Create {INPUT} with columns: name,address")
        print("Example row: MAK Accommodations,\"34 Dan Pienaar Street, Golfview, Mahikeng\"")
        sys.exit(1)

    out = open(OUTPUT, "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(out, fieldnames=["name", "address", "km", "minutes", "status"])
    writer.writeheader()

    ok = 0
    for i, row in enumerate(rows, 1):
        name = (row.get("name") or "").strip()
        address = (row.get("address") or "").strip()
        print(f"[{i}/{len(rows)}] {name[:40]}...", end=" ", flush=True)
        try:
            coords = geocode_photon(address)
            time.sleep(DELAY)
            if not coords:
                writer.writerow({"name": name, "address": address, "km": "", "minutes": "", "status": "geocode_fail"})
                print("geocode fail")
                continue
            km, mins = route_osrm(CAMPUS_LON, CAMPUS_LAT, coords[0], coords[1])
            time.sleep(0.3)
            if km is None:
                writer.writerow({"name": name, "address": address, "km": "", "minutes": "", "status": "route_fail"})
                print("route fail")
                continue
            writer.writerow({"name": name, "address": address, "km": km, "minutes": mins, "status": "ok"})
            print(f"{km} km, {mins} min")
            ok += 1
        except Exception as e:
            writer.writerow({"name": name, "address": address, "km": "", "minutes": "", "status": str(e)[:80]})
            print(f"ERR {e}")
            time.sleep(DELAY)

    out.close()
    print(f"\nDone. {ok}/{len(rows)} OK → {OUTPUT}")
    print("Paste km values into RESIDENCE_DISTANCE_KM in index.html, or send me distances.csv")


if __name__ == "__main__":
    main()
