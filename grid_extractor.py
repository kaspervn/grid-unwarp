import sys

import numpy as np
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt


def markers_from_file(svg_path):

    def get_marker_prop(xml_el):
        x, y = float(xml_el.attrib['cx']), float(xml_el.attrib['cy'])
        styles = dict(s.split(':') for s in xml_el.attrib['style'].split(';'))
        color_str = styles['fill']
        assert color_str[0] == '#'
        color = int(color_str[1:], base=16)

        return np.array([y, x]), color

    tree = ET.parse(svg_path)
    root = tree.getroot()
    all_circles = root.findall(".//{http://www.w3.org/2000/svg}ellipse") + root.findall(".//{http://www.w3.org/2000/svg}circle")
    return list(map(get_marker_prop, all_circles))



def closest_point(markers, p):
    return sorted(markers, key=lambda x: sum(np.abs(x[0] - p)))[0]


def follow_line(markers, start, dir, no_expected):
    result = []
    result.append(start)
    for n in range(no_expected-1):
        next = closest_point(markers, start[0] + dir)
        result.append(next)
        dir = next[0] - start[0]
        start = next

    return result


def follow_grid(markers, grid_size, origin, first_x, first_y):
    first_row = follow_line(markers,
                            start=origin,
                            dir=first_x[0] - origin[0],
                            no_expected=grid_size[1])

    first_column = follow_line(markers,
                               start=origin,
                               dir=first_y[0] - origin[0],
                               no_expected=grid_size[0])

    rows = [first_row]
    for n in range(1, grid_size[0]):
        rows.append(follow_line(markers,
                                  start=first_column[n],
                                  dir=rows[-1][1][0] - rows[-1][0][0],
                                  no_expected=grid_size[1]))
    return rows


def plot_grid(rows, grid_size, background_img=None, show=True, ax=None):
    columns = [[rows[y][x] for y in range(grid_size[0])] for x in range(grid_size[1])]

    if not ax:
        _, ax = plt.subplots()

    if background_img is not None:
        img = plt.imread(background_img)
        plt.imshow(img, cmap='gray')
        ax.set(ylim=(img.shape[0], 0), xlim=(0, img.shape[1]))


    def plot_line(line):
        ys = [p[0][0] for p in line]
        xs = [p[0][1] for p in line]
        ax.plot(xs, ys)

    for xline in rows:
        plot_line(xline)

    for yline in columns:
        plot_line(yline)

    if show:
        plt.show()


def track_grid_from_svg(svg_path, grid_size):
    color_types = {
        255+16711680: 'normal', # magenta
        65280: 'origin', # green
        16711680: 'first_x', # red
        255: 'first_y', # blue
    }

    markers = markers_from_file(svg_path)

    all_colors = set(m[1] for m in markers)

    assert len(all_colors) == len(color_types)

    markers_by_type = {color_types[color]: list(filter(lambda m: m[1] == color, markers)) for color in all_colors}

    expected_no_normal_dots = grid_size[0] * grid_size[1] - 3

    if len(markers_by_type['normal']) != expected_no_normal_dots:
        print(f"Warning: number of grid points in svg not as expected. Got {len(markers_by_type['normal'])} Expected {expected_no_normal_dots}", file=sys.stderr)
    assert(len(markers_by_type['origin']) == 1)
    assert(len(markers_by_type['first_x']) == 1)
    assert(len(markers_by_type['first_y']) == 1)

    return follow_grid(markers,
                       grid_size,
                       markers_by_type['origin'][0],
                       markers_by_type['first_x'][0],
                       markers_by_type['first_y'][0])

# some testing code to debug
if __name__ == '__main__':
    grid_size = (25, 23)
    rows = track_grid_from_svg('example.svg', grid_size)
    plot_grid(rows, grid_size, 'example.png')