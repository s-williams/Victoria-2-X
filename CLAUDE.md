# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Victoria 2: X is a total conversion mod for Paradox Interactive's Victoria 2. It aims to overhaul the entire Victoria 2 experience - map, countries, events, decisions, cultures, religions - replacing it with content from Egosoft's X Universe. The mod also aims to implement quality of life features.

## Validation Scripts
Python scripts in [scripts/](scripts/) validate mod consistency.

<!-- Note as of August 2026, check-provinces, check-ideologies, and check-terrains do not pass, they were copied over from another mod (TTA) and have yet to be re-implemented for X.-->

## File Encoding

**All localisation CSV files must be Windows-1252 encoded** (not UTF-8). Victoria 2 requires this. The `check-encoding.py` script enforces it. When editing localisation files, ensure your editor saves in Windows-1252 / cp1252.

**CLAUDE.md and all `.claude/skills/` files must use ASCII characters only** (no em-dashes, accented letters, curly quotes, or other non-ASCII), and must be saved as Windows-1252. All modders have their workstations configured to read files as Windows-1252, so any UTF-8 multi-byte sequences in these files will be misread.

## Architecture

### Victoria 2 Mod File Format

Most game data files use a custom Clausewitz-engine text format (`.txt`), not JSON/XML. The syntax is:

```
identifier = {
    key = value
    nested_block = {
        ...
    }
}
```

Comments use `#`. String values use `"quotes"` or bare words.

### Key Content Areas

| Directory | Purpose |
|-----------|---------|
| [common/](common/) | Core game definitions: countries, ideologies, governments, religions, cultures, goods, buildings, traits, CB types, defines.lua |
| [events/](events/) | Scripted events (`.txt`). Each event has an `id`, `trigger`, `mean_time_to_happen`, and `option` blocks |
| [decisions/](decisions/) | Player-selectable decisions (`.txt`). Have `potential`, `allow`, `effect` blocks |
| [history/countries/](history/countries/) | Starting conditions per country: ruling party, tech levels, reforms |
| [history/provinces/](history/provinces/) | Per-province starting state: owner, controller, pops, buildings |
| [localisation/](localisation/) | Windows-1252 CSV files mapping keys to displayed text. Format: `KEY;English text;;;;;;;;;` |
| [map/](map/) | Province definitions, regions, terrain, adjacencies, positions |
| [technologies/](technologies/) | Tech tree files |
| [inventions/](inventions/) | Invention unlocks triggered by technologies |
| [poptypes/](poptypes/) | Population type definitions must reference every ideology |
| [interface/](interface/) | UI layout files (`.gui`, `.gfx`) |
| [gfx/](gfx/) | Graphics assets |

#### Localisation files and special characters

All `localisation/*.csv` files must be written as Windows-1252, not UTF-8. The Edit tool writes UTF-8 and will silently corrupt any non-ASCII characters (e.g. accented letters in party names). Always use a Python script to modify these files:

```python
path = 'localisation/politics.csv'
with open(path, 'rb') as f:
    content = f.read().decode('cp1252')
anchor = 'existing_key;Existing Text;x\n'
insert = 'new_key;New Text with \u00fa (u-acute);x\n'  # \u00fa = cp1252 0xFA
content = content.replace(anchor, anchor + insert, 1)
with open(path, 'wb') as f:
    f.write(content.encode('cp1252'))
```

## Debugging Game Crashes

Steam's generic compatdata logs are NOT useful for this - do not trust logs under
`~/.local/share/Steam/steamapps/compatdata/Victoria 2/logs/` or
`~/.local/share/Steam/steamapps/compatdata/42960/pfx/.../Victoria II/logs/` (no mod
subfolder). Those are stale/unrelated (base game or old runs, may be months old).

The real, per-mod logs that get overwritten on every launch live at:
`~/.local/share/Steam/steamapps/compatdata/42960/pfx/drive_c/users/steamuser/Documents/Paradox Interactive/Victoria II/X/logs/`
(`setup.log`, `system.log`, `game.log`, `time.log`, etc. - 42960 is Victoria II's Steam
appid). Even a hard crash with no error dialog leaves partial logs behind - the last
line written tells you which loading phase failed (map init, database load, history
parse, the "Executing History" chronological replay, event load, etc.) even with no
explicit error message. `setup.log` in particular lists every history file loaded, in
order, right up to the crash point.

## Removing Provinces (map trimming)

Victoria 2's mod system silently falls back to the base game's file for anything not
overridden in the mod folder. When shrinking `map/definition.csv` / `map/provinces.bmp`
to remove unused provinces, the removed IDs can still crash the game via LEFTOVER
VANILLA DATA that references them, even after `map/`, `history/provinces/`, and
`history/countries/` all look clean. Checklist, in order:

1. `map/definition.csv` - trim to the IDs you keep. No gaps required, but no duplicate
   RGB colors allowed anywhere in the file (a duplicate color has caused a crash before,
   see git history around commit b838f91 "Somehow this works").
2. `map/provinces.bmp` - run `scripts/replace-province-colors.py` AFTER trimming
   `definition.csv`, so it recolors now-invalid pixels to a valid target color (default
   target matches province 1, "Space").
3. `map/default.map` - `max_provinces` must be >= highest surviving ID + 1, and
   `sea_starts` must not list IDs that no longer exist.
4. `map/region.txt`, `map/region_sea.txt`, `map/continent.txt` - check for stale
   references to removed IDs.
5. `history/provinces/<country>/` - vanilla files for removed IDs should be emptied
   (0 bytes), not deleted. This is the established convention in this repo even when the
   ID is not reused, so mod-fallback never pulls the vanilla file back in.
6. `history/pops/<date>/*.txt` - the one that actually caused a real crash here.
   Victoria 2 has multiple pop-history checkpoint dates (this mod uses `1836.1.1`,
   `1861.4.14`, `2990.1.1`). Each date folder holds one file per vanilla country
   (`Afghanistan.txt`, `Bermuda.txt`, ...), keyed directly by literal province ID
   (`2224 = { aristocrats = { ... } ... }`). These are easy to forget because they don't
   look like province/country history - but they were still the full, untouched vanilla
   dataset referencing thousands of removed province IDs, and the game crashed trying to
   populate pops into nonexistent provinces during the "Executing History" replay.
   Filter these files to keep only blocks whose leading ID is still valid (a brace-depth
   parse, not a naive line filter, since pop type blocks nest inside the province block).
   Only empty a file entirely if every block in it was for a removed province.
7. `history/wars/`, `history/units/`, `history/diplomacy/` - check these too if not
   fully populated by the mod. Empty files here fall back to vanilla, which references
   countries/provinces the mod doesn't have. Not confirmed to crash on its own, but worth
   checking first if problems resurface after fixing the above.

## Victoria 2 Modding Reference

**Always check the wiki before writing Clausewitz script** to avoid hallucinating invalid effects, conditions, or scopes.

### Core Scripting References
- [List of effects](https://vic2.paradoxwikis.com/List_of_effects) - used in `effect` blocks in events, decisions, and elsewhere
- [List of conditions](https://vic2.paradoxwikis.com/List_of_conditions) - used in `trigger`, `limit`, `allow`, `potential` blocks, and conditional things like CB types and news
- [List of scopes](https://vic2.paradoxwikis.com/List_of_scopes) - how to scope effects/conditions to a country, province, or pop

### Tutorials
- [Event modding](https://vic2.paradoxwikis.com/Event_modding)
- [How to make a decision](https://vic2.paradoxwikis.com/How_to_make_a_decision)
- [Creating a country](https://vic2.paradoxwikis.com/Creating_a_country)
- [Dynamic localisation](https://vic2.paradoxwikis.com/Dynamic_localisation)
- [IF Emulation](https://vic2.paradoxwikis.com/IF_Emulation)

