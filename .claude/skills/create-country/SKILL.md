---
name: create-country
description: Scaffold a new X-tag country (common/countries/, history/countries/, gfx/flags/) from the Xenon template once its tag exists (commented or not) in common/countries.txt. Use when the user says things like "create country <TAG>", "add country files for <name>", "do the same for <TAG>", or asks to scaffold/generate the country/history/flag entries for a tag already listed in common/countries.txt.
---

# Creating a new country

This mod's country-creation workflow is split between the user and Claude:

- **User does:** adds (or already has, possibly commented out) the `TAG = "countries/<Name>.txt"` line in `common/countries.txt`.
- **Claude does:** everything downstream of that - the `common/countries/<Name>.txt` definition, `history/countries/<TAG> - <Name>.txt`, and the 5 `gfx/flags/<TAG>*.tga` textures.

`Xenon.txt` / `XEN - Xenon.txt` / the `XEN*.tga` flags are the house template - always copy from them (not from a heavily customized country like GOD) so party dates, reform defaults, and structure stay consistent with the rest of the mod.

## Steps

1. **Resolve tag and name from `common/countries.txt`.** Find the `TAG = "countries/<Name>.txt"` line (it may be commented out with a leading `#`). The `<Name>` (without `.txt`) is the exact filename to use everywhere below - do not paraphrase or re-title it. If the tag isn't in the file at all, add it under the most fitting faction group (the file is organized into `# <Faction>` sections, not strictly alphabetical despite the header comment) or ask the user where it belongs.

2. **Create `common/countries/<Name>.txt`** by copying `common/countries/Xenon.txt` and:
   - Replacing the `color = { r g b }` line with a new random RGB triple (each channel roughly 20-235 so it isn't too dark/light). Spot-check it isn't a near-duplicate of an obviously adjacent country's color (e.g. via `grep -h "^color" common/countries/*.txt`), but an exhaustive uniqueness check isn't necessary.
   - Replacing every `XEN_conservative` with `<TAG>_conservative`.
   - Leaving `start_date`/`end_date` as-is (currently `2990.1.1` / `4000.1.1` in the template) and everything else (graphical_culture, policies, `unit_names = {}`) untouched.

3. **Create `history/countries/<TAG> - <Name>.txt`** by copying `history/countries/XEN - Xenon.txt` and replacing `ruling_party = XEN_conservative` with `ruling_party = <TAG>_conservative`. Everything else (capital, culture, religion, reforms, upper_house weights) is copied verbatim from the Xenon template as placeholder scaffolding - flag to the user that these values (especially `capital` - Xenon's `354` is not a real capital for the new country) are placeholders they'll likely want to customize for lore accuracy, since picking a real capital/culture/religion needs game knowledge this skill doesn't have.

4. **Copy the 5 flag files**, renaming the `XEN` prefix to `<TAG>`:
   `XEN.tga`, `XEN_communist.tga`, `XEN_fascist.tga`, `XEN_monarchy.tga`, `XEN_republic.tga` -> same suffixes with `<TAG>`.

5. **Uncomment the line in `common/countries.txt`** if it started commented out (strip the leading `#`), unless the user has said they want it left inactive for now.

6. **Verify** none of the target paths already existed before you wrote them (don't silently overwrite a hand-customized country), and that the tag/name pairing is consistent across all three locations.

## Notes

- No validation script exists yet for country consistency (unlike `scripts/check-provinces.py` for provinces) - double-check tag/filename consistency by eye.
- No localisation entries for country names currently exist for any tag (checked GOD and XEN) - this skill does not add them; only mention it if the user asks about display names in-game.
- This same recipe applies whether scaffolding one tag or a whole batch of commented-out tags at once - repeat steps 2-5 per tag.
