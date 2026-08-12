import argparse

from PIL import Image

definition_file = "map/definition.csv"
provinces_bmp_file = "map/provinces.bmp"


def parse_color(s):
    parts = s.split(',')
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(f'"{s}" is not a valid r,g,b color')
    try:
        r, g, b = (int(p) for p in parts)
    except ValueError:
        raise argparse.ArgumentTypeError(f'"{s}" is not a valid r,g,b color')
    return (r, g, b)


"""
Get every valid province color listed in map/definition.csv
"""
def parse_definition_colors():
    colors = set()
    with open(definition_file, 'r', encoding='windows-1252') as f:
        lines = f.readlines()
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.rstrip('\n').split(';')
        if len(parts) < 5:
            continue
        colors.add((int(parts[1]), int(parts[2]), int(parts[3])))
    return colors


"""
Replace every pixel in map/provinces.bmp whose color has no entry in map/definition.csv
with the target color, saving the result back in place.
"""
def main():
    parser = argparse.ArgumentParser(
        description='Replace colors in map/provinces.bmp that have no entry in map/definition.csv '
                     'with a target color.')
    parser.add_argument('--target', type=parse_color, default=(41, 201, 201),
                         help='replacement color, as r,g,b (default: 41,201,201)')
    args = parser.parse_args()

    valid_colors = parse_definition_colors()

    img = Image.open(provinces_bmp_file).convert('RGB')
    pixels = img.load()
    width, height = img.size

    counts = {}
    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            if pixel not in valid_colors and pixel != args.target:
                pixels[x, y] = args.target
                counts[pixel] = counts.get(pixel, 0) + 1

    if not counts:
        print('No matching pixels found, file left unchanged.')
        return

    for color, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f'{color} -> {args.target}: {count} pixels replaced')

    img.save(provinces_bmp_file)
    print(f'Saved {provinces_bmp_file}')


if __name__ == '__main__':
    main()
