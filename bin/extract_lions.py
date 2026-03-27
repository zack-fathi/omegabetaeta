#!/usr/bin/env python3
"""Extract unique lion names from insert_brothers.sql."""
import re

with open("sql/insert_brothers.sql") as f:
    content = f.read()

lion_names = set()
for match in re.finditer(r'lion_name, active.*?VALUES\((.+?)\);', content, re.DOTALL):
    vals = match.group(1)
    parts = re.findall(r'"([^"]*?)"', vals)
    if len(parts) >= 6:
        lion_names.add(parts[5])

for n in sorted(lion_names):
    print(n)
