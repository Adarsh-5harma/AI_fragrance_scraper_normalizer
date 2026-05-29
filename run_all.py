import csv, os

sources = [
    "data/lodoro_raw.csv",
    "data/multimarcas_raw.csv",
]

all_rows = []
for path in sources:
    with open(path) as f:
        all_rows.extend(list(csv.DictReader(f)))

# Deduplicate by source_url (keep first seen)
seen = set()
deduped = []
for row in all_rows:
    key = row["source_url"]
    if key not in seen:
        seen.add(key)
        deduped.append(row)

with open("data/master_catalog.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
    writer.writeheader()
    writer.writerows(deduped)

print(f"Master catalog: {len(deduped)} rows from {len(all_rows)} total")