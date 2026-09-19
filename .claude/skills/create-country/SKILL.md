---
name: create-country
description: Scaffold a new X-tag country (common/countries/, history/countries/, common/country_colors.txt, gfx/flags/, and starting-province ownership/cores when given) from the Xenon template once its tag exists (commented or not) in common/countries.txt. Use when the user says things like "create country <TAG>", "add country files for <name>", "do the same for <TAG>", or asks to scaffold/generate the country/history/flag/color/province entries for a tag already listed in common/countries.txt.
---

# Creating a new country

This mod's country-creation workflow is split between the user and Claude:

- **User does:** adds (or already has, possibly commented out) the `TAG = "countries/<Name>.txt"` line in `common/countries.txt`. May also drop a hand-made base flag at `gfx/flags/<TAG>.tga` ahead of time, and/or name starting province(s) for the country in the prompt.
- **Claude does:** everything downstream of that - the `common/countries/<Name>.txt` definition, `history/countries/<TAG> - <Name>.txt`, a `common/country_colors.txt` entry, the `gfx/flags/<TAG>*.tga` textures, and (when province info is given) the relevant `history/provinces/**/<ID> - <ProvinceName>.txt` ownership/core lines.

`Xenon.txt` / `XEN - Xenon.txt` / the `XEN*.tga` flags are the default house template - copy from them (not from a heavily customized country like GOD) so party dates, reform defaults, and structure stay consistent with the rest of the mod, *unless* the user names a different source country to copy from (see "Copying from a non-Xenon source" below).

## Two party archetypes

Countries in this mod use one of two party-block shapes in their `common/countries/<Name>.txt`, and the shape determines what `ruling_party` in the history file must reference:

- **Unique-party (Xenon-style):** one `party = { name = "<TAG>_<ideology>" ... }` block, tag-prefixed. Xenon itself only has `XEN_fascist` (single fascist party) - there is no `XEN_conservative`, despite what an earlier version of this skill assumed. Used for single-ideology/hive-like factions.
- **Generic-party (most countries):** six `party` blocks named `generic_reactionary`, `generic_conservative`, `generic_liberal`, `generic_anarcho_liberal`, `generic_socialist`, `generic_communist` - identical boilerplate copied into nearly every non-Xenon country file (Yaki, Argon Federation, Boron, etc). `ruling_party` in these countries' history files points at one of these generic names, not a tag-prefixed one.

Default to the Xenon (unique-party) template. **If the user says to copy the history/flavor from a different existing country**, check which archetype that source country uses (grep its `common/countries/<Name>.txt` for `party = {`) and mirror that same party block into the new country's `common/countries/<Name>.txt` too - not Xenon's. Otherwise the new history file's `ruling_party` (copied from the source) won't resolve to any party the new country actually defines.

## Steps

1. **Resolve tag and name from `common/countries.txt`.** Find the `TAG = "countries/<Name>.txt"` line (it may be commented out with a leading `#`). The `<Name>` (without `.txt`) is the exact filename to use everywhere below - do not paraphrase or re-title it. If the tag isn't in the file at all, add it under the most fitting faction group (the file is organized into `# <Faction>` sections, not strictly alphabetical despite the header comment) or ask the user where it belongs.

2. **Create `common/countries/<Name>.txt`.** Copy `common/countries/Xenon.txt` by default:
   - Replace the `color = { r g b }` line with a new RGB triple. If the user gives a specific color, use it verbatim even if dark/light; otherwise pick one with each channel roughly 20-235 so it isn't too dark/light. Spot-check it isn't a near-duplicate of an obviously adjacent country's color (e.g. via `grep -h "^color" common/countries/*.txt`), but an exhaustive uniqueness check isn't necessary.
   - Replace `XEN_fascist` with `<TAG>_fascist` (or whatever the template's actual party name is - don't assume `_conservative`).
   - Leave `start_date`/`end_date` as-is (currently `2990.1.1` / `4000.1.1`) and everything else (graphical_culture, policies, `unit_names = {}`) untouched.
   - **If copying from a non-Xenon source instead** (see above), copy that source's full party block(s) verbatim (these use `generic_*` names, so no renaming needed) rather than Xenon's single party.

3. **Create `history/countries/<TAG> - <Name>.txt`.** Copy `history/countries/XEN - Xenon.txt` by default and replace `ruling_party = XEN_fascist` with `ruling_party = <TAG>_fascist`. Everything else (capital, culture, religion, reforms, upper_house weights) is copied verbatim from the Xenon template as placeholder scaffolding - flag to the user that these values (especially `capital` - Xenon's `354` is not a real capital for the new country) are placeholders they'll likely want to customize for lore accuracy, since picking a real capital/culture/religion needs game knowledge this skill doesn't have.
   - **If the user names a different source country** (e.g. "copy history from Yaki"), copy that country's history file verbatim instead, including its `ruling_party` value unchanged (it'll be a `generic_*` name that now resolves correctly because step 2 copied the matching party block too). Still flag placeholder fields like `capital` the same way.

4. **If the prompt names starting province(s) for the country, update their `history/provinces/**/<ID> - <ProvinceName>.txt` files.** Locate the file with e.g. `find history/provinces -iname "<ID> - *"` (region subfolder, e.g. `x/`, `usa/`, isn't predictable from the ID alone). A province file's relevant lines look like:
   ```
   owner = <TAG>
   controller = <TAG>
   add_core = <TAG>
   ```
   - **If the country should own the province at start** (e.g. "starting province is X", "capital is province X"), set `owner = <TAG>` and `controller = <TAG>` (overwriting whatever tag was there), and add `add_core = <TAG>` if not already present. Leave every other line (`trade_goods`, `life_rating`, `terrain`, other tags' `add_core` lines) untouched.
   - **If the country should merely hold a core/claim on the province without owning it** (e.g. "core claim on X", "claims province X"), leave `owner`/`controller` untouched and only add an `add_core = <TAG>` line - don't overwrite the existing owner. This is a real, intentional pattern in this mod: Beryll's `140 - Outer Sol XI.txt` keeps `owner = TER` / `controller = TER` while adding `add_core = BYL` (core claim on Terran territory), matching `capital = 140` in `BYL - Beryll.txt` even though Beryll doesn't own its own capital province at start.
   - Cross-check against the `capital = <ID>` field already written in the country's own history file. If they don't match, or the country's capital province ends up not owned by the country (as in the Beryll example above), don't silently "fix" it - flag the discrepancy to the user, since owned-vs-core-only is a deliberate lore choice this skill can't judge on its own.

5. **Add an entry to `common/country_colors.txt`.** Format:
   ```
   # <Name>
   <TAG> = {
       color1 = { r g b }
       color2 = { r g b }
       color3 = { r g b }
   }
   ```
   - `color1` should match the `color = {...}` used in `common/countries/<Name>.txt` (use the user's exact value if they gave one).
   - Pick `color2`/`color3` to complement `color1`, judging by nearby examples in the file - e.g. a near-black base (like Dukes Buccaneers, `BUC`) pairs with lighter/darker grayscale tints of itself, while more saturated bases (like Yaki, `YAK`) pair with contrasting hues instead. Don't just default to a formula; look at what similar-toned entries in the file already do.
   - Insert the block in the same relative position as the tag's entry in `common/countries.txt` (this file mirrors that faction-group ordering, not strict alphabetical) - e.g. a tag added right after `YAK` in `common/countries.txt` goes right after `YAK`'s block here too.

6. **Copy the flag files.** Check whether `gfx/flags/<TAG>.tga` already exists first:
   - **If it already exists** (the user pre-supplied custom art), leave it untouched and derive the 4 government-variant flags by copying *that* file to `<TAG>_communist.tga`, `<TAG>_fascist.tga`, `<TAG>_monarchy.tga`, `<TAG>_republic.tga`.
   - **If it doesn't exist**, copy all 5 from the `XEN` template (`XEN.tga`, `XEN_communist.tga`, `XEN_fascist.tga`, `XEN_monarchy.tga`, `XEN_republic.tga`), renaming the prefix to `<TAG>`.

7. **Uncomment the line in `common/countries.txt`** if it started commented out (strip the leading `#`), unless the user has said they want it left inactive for now.

8. **Add localisation, only if the user explicitly asks for a display name.** Country name localisation lives in `localisation/politics.csv`, ordered strictly alphabetically by tag (unlike `common/countries.txt`/`common/country_colors.txt`, which follow faction grouping - don't mix up the two ordering conventions). At minimum, add:
   ```
   <TAG>_ADJ;<Adjective>;x
   <TAG>;<Display Name>;x
   ```
   Some countries (Xenon, Argon, Antigone, Zyarth, ...) also carry per-government-form flavor names, e.g. `<TAG>_absolute_monarchy;...;x`, `<TAG>_presidential_dictatorship;...;x` - add these only if the user wants that level of flavor text; otherwise the two base lines are sufficient. This file must stay Windows-1252 - use the CLAUDE.md python snippet (read/decode `cp1252`, string-replace, encode/write `cp1252`), never the Edit tool.

9. **Verify** none of the target paths already existed before you wrote them (don't silently overwrite a hand-customized country or a user-supplied flag), and that the tag/name pairing is consistent across all locations.

## Notes

- No validation script exists yet for country consistency (unlike `scripts/check-provinces.py` for provinces) - double-check tag/filename consistency by eye.
- This same recipe applies whether scaffolding one tag or a whole batch of commented-out tags at once - repeat steps 2-8 per tag.
