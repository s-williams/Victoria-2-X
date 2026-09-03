import argparse
import csv
import os
import re
import sys

provinces_csv_file = 'dev/scripts/utility/provinces.csv'
cultures_file = 'common/cultures.txt'
religion_file = 'common/religion.txt'
production_types_file = 'common/production_types.txt'
provinces_history_dir = 'history/provinces/x'
output_file = 'history/pops/2990.1.1/x.txt'

POP_TYPE_COLUMNS = [
    'aristocrats', 'capitalists', 'bureaucrats', 'officers', 'soldiers',
    'clergymen', 'artisans', 'clerks', 'craftsmen', 'slaves',
]

RELIGION_OVERRIDES = {
}


"""
Parse common/cultures.txt into {culture_name: group_name}, where group_name
has the trailing "_group" stripped (e.g. "human_group" -> "human").
"""
def parse_cultures():
    with open(cultures_file, 'r', encoding='windows-1252') as f:
        content = f.read()
    culture_to_group = {}
    group = None
    depth = 0
    for line in content.split('\n'):
        stripped = line.split('#', 1)[0].strip()
        if not stripped:
            continue
        m = re.match(r'^(\w+)\s*=\s*\{', stripped)
        if m and depth == 0:
            group = m.group(1)
            depth += stripped.count('{') - stripped.count('}')
            continue
        if depth == 1:
            m = re.match(r'^(\w+)\s*=\s*\{', stripped)
            if m:
                culture_to_group[m.group(1)] = re.sub(r'_group$', '', group)
        depth += stripped.count('{') - stripped.count('}')
        if depth <= 0:
            group = None
            depth = 0
    return culture_to_group


"""
Parse common/religion.txt for the set of valid religion/species names
(every leaf entry across every top-level group, e.g. "human", "paranid", "agi").
"""
def parse_religions():
    with open(religion_file, 'r', encoding='windows-1252') as f:
        content = f.read()
    religions = set()
    depth = 0
    for line in content.split('\n'):
        stripped = line.split('#', 1)[0].strip()
        if not stripped:
            continue
        m = re.match(r'^(\w+)\s*=\s*\{', stripped)
        if m and depth == 1:
            religions.add(m.group(1))
        depth += stripped.count('{') - stripped.count('}')
    return religions


"""
Parse common/production_types.txt RGO section for {output_good: 'farmers'|'labourers'},
based on each RGO's farm=yes / mine=yes flag.
"""
def parse_good_labor_types():
    with open(production_types_file, 'r', encoding='windows-1252') as f:
        content = f.read()
    good_to_labor = {}
    for block in re.finditer(r'(\w+)\s*=\s*\{([^{}]*)\}', content):
        body = block.group(2)
        good_m = re.search(r'output_goods\s*=\s*(\w+)', body)
        if not good_m:
            continue
        if re.search(r'farm\s*=\s*yes', body):
            good_to_labor[good_m.group(1)] = 'farmers'
        elif re.search(r'mine\s*=\s*yes', body):
            good_to_labor[good_m.group(1)] = 'labourers'
    return good_to_labor


"""
Build {province_id: trade_good} by scanning history/provinces/x/*.txt filenames
for their leading ID and reading the trade_goods line inside.
"""
def parse_province_trade_goods():
    trade_goods = {}
    for fn in os.listdir(provinces_history_dir):
        m = re.match(r'(\d+) - ', fn)
        if not m:
            continue
        pid = int(m.group(1))
        with open(os.path.join(provinces_history_dir, fn), 'r', encoding='windows-1252') as f:
            content = f.read()
        gm = re.search(r'^trade_goods\s*=\s*(\w+)', content, re.M)
        if gm:
            trade_goods[pid] = gm.group(1)
    return trade_goods


"""
Parse a "50 argon 50 boron" style breakdown string into [(culture, fraction), ...],
where fraction is the percentage divided by 100.
"""
def parse_breakdown(bd_string):
    parts = bd_string.split()
    pairs = []
    for i in range(0, len(parts) - 1, 2):
        pairs.append((parts[i + 1], float(parts[i]) / 100.0))
    return pairs


def main():
    parser = argparse.ArgumentParser(
        description='Generate history/pops/2990.1.1/x.txt from scripts/utility/provinces.csv.')
    parser.add_argument('--dry-run', action='store_true',
                         help='validate and report only, do not write the output file')
    args = parser.parse_args()

    culture_to_group = parse_cultures()
    valid_religions = parse_religions()
    good_to_labor = parse_good_labor_types()
    trade_goods = parse_province_trade_goods()

    def religion_for_culture(culture):
        group = culture_to_group.get(culture)
        if group is None:
            return None
        return RELIGION_OVERRIDES.get(group, group)

    with open(provinces_csv_file, 'r', encoding='windows-1252', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        rows = list(reader)

    errors = []
    warnings = []
    all_cultures_used = set()
    blocks = []

    for row in rows:
        pid = int(row['ID'])
        name = row['Name']

        try:
            total_pop = float(row['total_pop'])
        except (TypeError, ValueError):
            errors.append(f'{pid} ({name}): total_pop is missing or not a number')
            continue

        entries = []  # (pop_type, culture, religion, size)
        pc_sum = 0.0

        for col in POP_TYPE_COLUMNS:
            pc_raw = row.get(f'{col}_pc', '').strip()
            bd_raw = row.get(f'{col}_bd', '').strip()
            if not pc_raw:
                continue
            try:
                pc = float(pc_raw)
            except ValueError:
                errors.append(f'{pid} ({name}): {col}_pc "{pc_raw}" is not a number')
                continue
            pc_sum += pc
            if not bd_raw:
                errors.append(f'{pid} ({name}): {col}_pc is set but {col}_bd is empty')
                continue
            breakdown = parse_breakdown(bd_raw)
            bd_total = sum(frac for _, frac in breakdown) * 100
            if abs(bd_total - 100) > 0.5:
                errors.append(f'{pid} ({name}): {col}_bd sums to {bd_total:.1f}, not 100')
            for culture, frac in breakdown:
                size = round(total_pop * (pc / 100.0) * frac)
                if size <= 0:
                    continue
                entries.append((col, culture, frac, size))

        if pc_sum > 100 + 0.5:
            errors.append(f'{pid} ({name}): pop-type percentages sum to {pc_sum:.1f}, over 100')
            continue

        fl_pc_raw = row.get('farmers_labourers_pc', '').strip()
        fl_bd_raw = row.get('farmers_labourers_bd', '').strip()
        if fl_pc_raw and fl_pc_raw.lower() != 'rest':
            errors.append(f'{pid} ({name}): farmers_labourers_pc should be "rest", got "{fl_pc_raw}"')
        if fl_bd_raw:
            good = trade_goods.get(pid)
            if good is None:
                warnings.append(f'{pid} ({name}): no history/provinces file found, skipping province')
                continue
            labor_type = good_to_labor.get(good)
            if labor_type is None:
                errors.append(f'{pid} ({name}): trade good "{good}" has no farm/mine RGO in production_types.txt')
                continue
            rest_pc = 100.0 - pc_sum
            breakdown = parse_breakdown(fl_bd_raw)
            bd_total = sum(frac for _, frac in breakdown) * 100
            if abs(bd_total - 100) > 0.5:
                errors.append(f'{pid} ({name}): farmers_labourers_bd sums to {bd_total:.1f}, not 100')
            for culture, frac in breakdown:
                size = round(total_pop * (rest_pc / 100.0) * frac)
                if size <= 0:
                    continue
                entries.append((labor_type, culture, frac, size))

        for _, culture, _, _ in entries:
            all_cultures_used.add((pid, name, culture))

        if entries:
            blocks.append((pid, entries))

    for pid, name, culture in sorted(all_cultures_used):
        if culture not in culture_to_group:
            errors.append(f'{pid} ({name}): unrecognised culture "{culture}", not defined in {cultures_file}')

    for pid, name, culture in sorted(all_cultures_used):
        religion = religion_for_culture(culture)
        if religion is not None and religion not in valid_religions:
            errors.append(f'{pid} ({name}): culture "{culture}" maps to religion "{religion}", '
                           f'not defined in {religion_file}')

    if warnings:
        print(f'{len(warnings)} warning(s):')
        for w in warnings:
            print(f'  {w}')

    if errors:
        print(f'{len(errors)} error(s), aborting:', file=sys.stderr)
        for e in errors:
            print(f'  {e}', file=sys.stderr)
        sys.exit(1)

    lines = []
    for pid, entries in sorted(blocks):
        lines.append(f'{pid} = {{')
        for pop_type, culture, _, size in entries:
            religion = religion_for_culture(culture)
            lines.append(f'\t{pop_type} = {{')
            lines.append(f'\t\tculture = {culture}')
            lines.append(f'\t\treligion = {religion}')
            lines.append(f'\t\tsize = {size}')
            lines.append('\t}')
        lines.append('}')
    content = '\n'.join(lines) + '\n'

    if args.dry_run:
        print(f'Validation passed. {len(blocks)} provinces would be written to {output_file}.')
        return

    with open(output_file, 'w', encoding='windows-1252', newline='\n') as f:
        f.write(content)
    print(f'Wrote {len(blocks)} provinces to {output_file}.')


if __name__ == '__main__':
    main()
