import json


def parse_coords(values):
    values = values[values.index('=') + 2:].split(',')
    if values[-1] == '':
        values = values[:-1]
    return list(map(float, values))


if __name__ == '__main__':
    lines = None
    with open('resources/polygons/triad.txt', 'r') as f:
        lines = f.readlines()

    if lines is None:
        print('Could not read file!')
    else:
        entire_dict = {
            "uuid": "2bee0dc9-4ffe-519b-1cbd-7fbe763a6047",
            "mapId": "/Game/Maps/Triad/Triad",
            "displayName": "Haven",
            "mapImage": "resources/maps/triad.png",
            "backgroundImage": "resources/maps/triad_background.png",
            "multiplier": {
                "x": 0.000075,
                "y": -0.000075
            },
            "offset": {
                "x": 1.09345,
                "y": 0.642728
            },
            'zones': []
        }

        i = 0
        while i < len(lines):
            line: str = lines[i]
            if line.startswith('#'):  # Map area title
                zone_name = line.strip()[1:]
                print(f'Storing polygons for "{zone_name}"')

                x_values = parse_coords(lines[i + 1])
                y_values = parse_coords(lines[i + 2])
                print(f'x: {x_values}')
                print(f'y: {y_values}')

                zone_info = {
                    'name': zone_name,
                    'points': []
                }
                for x, y in zip(x_values, y_values):
                    zone_info['points'].append({
                        'x': x,
                        'y': y
                    })
                entire_dict['zones'].append(zone_info)
                i += 3
        with open('resources/maps/triad.json', 'w') as f:
            f.write(json.dumps(entire_dict, indent=2))
