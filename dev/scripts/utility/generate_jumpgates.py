import csv
import re

region_file = 'map/region.txt'
event_modifiers_file = 'common/event_modifiers.txt'
adjacencies_file = 'map/adjacencies.csv'


"""
Parse map/region.txt into {province_id: region_key}, where region_key is the
REG_ name lowercased with the prefix stripped (REG_KINGDOM_END -> kingdom_end).
"""
def parse_regions():
    province_to_region = {}
    with open(region_file, 'r', encoding='windows-1252') as f:
        for line in f:
            line = line.strip()
            m = re.match(r'^(REG_[A-Z0-9_]+)\s*=\s*\{([^}]*)\}', line)
            if not m:
                continue
            region_key = m.group(1)[len('REG_'):].lower()
            for province_id in m.group(2).split():
                province_to_region[int(province_id)] = region_key
    return province_to_region


"""
Parse common/event_modifiers.txt for the set of defined jumpgate_to_* modifier names.
"""
def parse_jumpgate_modifiers():
    with open(event_modifiers_file, 'r', encoding='windows-1252') as f:
        content = f.read()
    return set(re.findall(r'^(jumpgate_to_[a-z0-9_]+)\s*=\s*\{', content, re.MULTILINE))


"""
Parse map/adjacencies.csv into a list of (from_province, to_province) int pairs.
"""
def parse_adjacencies():
    pairs = []
    with open(adjacencies_file, 'r', encoding='windows-1252') as f:
        reader = csv.reader(f, delimiter=';')
        header = next(reader)
        for row in reader:
            if not row or not row[0].strip():
                continue
            pairs.append((int(row[0]), int(row[1])))
    return pairs


def main():
    province_to_region = parse_regions()
    valid_modifiers = parse_jumpgate_modifiers()
    pairs = parse_adjacencies()

    lines = []
    for from_id, to_id in pairs:
        from_region = province_to_region.get(from_id)
        to_region = province_to_region.get(to_id)
        if from_region is None:
            raise ValueError(f'province {from_id} not found in any region')
        if to_region is None:
            raise ValueError(f'province {to_id} not found in any region')
        if from_region == to_region:
            print(f'# skipping {from_id} <-> {to_id}: both in region {from_region}')
            continue

        for province_id, dest_region in ((from_id, to_region), (to_id, from_region)):
            modifier_name = f'jumpgate_to_{dest_region}'
            if modifier_name not in valid_modifiers:
                raise ValueError(f'{modifier_name} is not defined in {event_modifiers_file}')
            lines.append(
                f'{province_id} = {{ add_province_modifier = {{ name = {modifier_name} duration = -1 }} }}'
            )

    print('\n'.join(lines))


if __name__ == '__main__':
    main()
