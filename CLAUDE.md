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
| [technologies/](technologies/) | 7 tech tree files (army, navy, commerce, diplomacy, military_theory, knowledge, population) |
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

