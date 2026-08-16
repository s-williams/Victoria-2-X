---
name: create-province
description: Wire up new X-tag provinces after the user has added them to map/definition.csv and provinces.bmp - creates history files, updates map/region.txt, and fills in localisation/map.csv. Use when the user says things like "create/add province(s) <name> <id range>", "do the same for <region name> <id range>", or asks to fill in region.txt / map.csv for provinces already in definition.csv.
---

# Creating basic provinces

This mod's province-creation workflow is split between the user and Claude:

- **User does:** adds the new province row(s) to `map/definition.csv` (id, color, name, tag) and paints the matching pixels in `map/provinces.bmp`.
- **Claude does:** everything downstream of that - history files, `map/region.txt`, and `localisation/map.csv`.

`map/definition.csv` is the source of truth for province IDs and exact name spelling (apostrophes, capitalization, etc). Always read the current rows for the given ID range from there before creating anything - do not trust a name typed in chat if it conflicts with definition.csv, and do not trust a region name in region.txt if the user says it changed. Because this project's `grep` is aliased to `ugrep`, which silently skips this ISO-8859/cp1252 file as "binary", use `awk -F';' '$1+0>=START && $1+0<=END {print $1";"$5}' map/definition.csv` or `sed`/`grep -a` to read it, never plain `grep`.

Some new province IDs reuse numbers that used to belong to vanilla Victoria 2 provinces (e.g. old USA/Mexico Texas provinces reused for X-universe "Outer Sol"). The old vanilla history file (e.g. `history/provinces/usa/133 - Austin.txt`) is left in place but emptied to 0 bytes - this is intentional and not a conflict, so do not delete, rename, or flag these files. Only create the new file under `history/provinces/x/`.

## Steps

1. **Read the definition.csv rows for the given ID range, plus the row immediately before it.** Confirm the count of provinces and the exact name text (including apostrophes) for each. Check two things before creating anything:
   - **Internal gaps:** the ids from the first to the last province in this batch must be strictly sequential with no gaps (e.g. a 7-province region must occupy 7 consecutive ids).
   - **Leading gap:** the id immediately before the batch's first id must belong to the immediately preceding province entry in definition.csv (i.e. `<batch's first id> - 1` must actually exist as a row). A jump straight to this batch's first id from something lower (e.g. the previous entry is id 230 and this batch starts at 232, skipping 231) means definition.csv is still being edited.

   If either check fails, stop and ask the user how to proceed rather than guessing or working around it; do not create any files for that batch yet. A gap immediately *after* the batch's last id (leading into whatever comes next in the file) is fine and not blocking, since it isn't this batch's concern - just note it to the user in passing.

2. **Create `history/provinces/x/<id> - <Name>.txt`** for each new province. Match the id/name exactly as it appears in definition.csv. Baseline content, CRLF line endings:
   ```
   trade_goods = fish
   life_rating = 25
   ```
   Only add `owner = <TAG>`, `controller = <TAG>`, `add_core = <TAG>` lines (in that order, before trade_goods) if the user explicitly asks for an owner/controller/core - otherwise leave them out. Check a sibling file in the same region for the current template/line-ending convention before assuming CRLF, since these have occasionally been hand-edited to LF.

3. **Update `map/region.txt`.** Each region is one line: `REG_<NAME> = { id id id ... }`. Derive `<NAME>` from the province base name (without the roman numeral) by:
   - stripping apostrophes (`Rhy's Defiance` -> `RHYS_DEFIANCE`, not `RHY_S_DEFIANCE`)
   - uppercasing and replacing spaces with underscores
   Many `REG_*` lines already exist pre-declared but empty (`REG_FOO = { }`) under geography-section headers (`# Boron (Northwest)`, `# Zyarth (North)`, etc) - fill in the existing empty line rather than adding a new one if one already matches. Only append a new line if no placeholder exists.

4. **Update `localisation/map.csv`.** Two sections, each delimited by `{ ... }` comment markers:
   - Provinces block: add `PROV<id>;<Name>;x` for each new province, keeping numeric id order.
   - Regions block: add `REG_<NAME>;<Display Name>;x` (display name = the province base name with apostrophes intact, e.g. `Rhy's Defiance`) if this region doesn't already have a line.
   This file must stay ASCII/Windows-1252 safe like other localisation CSVs - province names here are English text with plain straight apostrophes only, so the Edit tool is fine as long as no curly quotes or accents are introduced.

5. **Cross-check names once more** across definition.csv, the new file names, region.txt, and map.csv before finishing - apostrophe placement and typos (e.g. "Arteus'" vs "Atreus'", "Heretic's" vs "Heretics") have drifted before. If you find an existing mismatch outside the current task's scope, flag it to the user rather than silently renaming unrelated files.

## Reference

`scripts/check-provinces.py` is intended to validate exactly this consistency (definition.csv, history files, region.txt, map.csv) but per CLAUDE.md is not currently passing/re-implemented for this mod - do not rely on it as a safety net yet.
