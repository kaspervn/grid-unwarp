import argparse
import multiprocessing
from pathlib import Path

import grid_extractor
import unwarp

argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
argparser.add_argument('--destination-folder', type=Path, help='If set, original filenames are used. Else the files are stored in the current directory with the prefix "unwarped"')
argparser.add_argument('--output-format', default='png', help='jpg, png, tiff, etc ... Can be any format supported by imageio')
argparser.add_argument('--processes', default=4, type=int, help='Number of simultaneous processes')
argparser.add_argument('calibration_svg')
argparser.add_argument('grid_size_x', type=int)
argparser.add_argument('grid_size_y', type=int)
argparser.add_argument('output_pixels_per_grid_unit', type=int)
argparser.add_argument('input_files', nargs='+', type=Path)

args = argparser.parse_args()

output_extension = args.output_format  if args.output_format[0] == '.' else '.' + args.output_format


if args.destination_folder is not None:
    args.destination_folder.mkdir(exist_ok=True)
    filename_convert = lambda p: args.destination_folder.joinpath(p.stem + output_extension)
else:
    filename_convert = lambda p: p.parent.joinpath('unwarped_' + p.stem + output_extension)

grid_size = (args.grid_size_x, args.grid_size_y)

print('determining grid lines')
grid_data = grid_extractor.track_grid_from_svg(args.calibration_svg, grid_size)
map_point = unwarp.scipy_interpolate_fit(grid_data, grid_size)

print('calculating coordinate map')
unwarp_params = unwarp.calculate_coordinate_map(map_point, grid_size, args.output_pixels_per_grid_unit)

def process_image(f: Path):
    output_path = filename_convert(f)
    assert output_path != f
    print(f'{f} -> {output_path}')
    unwarp.unwarp_image(f, output_path, *unwarp_params)

with multiprocessing.Pool(processes=args.processes) as p:
    p.map(process_image, args.input_files)