# Chart calculator
Setup (once): `pip install pyswisseph timezonefinder geopy`
Run: `python chart_calc.py --name Jane --date 1985-03-14 --time 14:07 --place "Kansas City, Missouri, USA" --out jane`
Or with coordinates: `--lat 39.0997 --lon -94.5786` (use if place lookup fails). Optional: `--tz America/Chicago`, `--asof 2026-11-17`.
Output: jane.json and jane.md (give the .md to the AI to write the reading from). Read any CHECK lines before you trust the chart.
