import argparse
import multiprocessing
from pathlib import Path
from glob import glob
from more_itertools import flatten

from execution_time import ExecutionTime

import grid_extractor
import unwarp
import platform

exec_timer = ExecutionTime()

@exec_timer.timeit
def prepare_coordinate_map(args):
    print('determining grid lines')
    grid_data = grid_extractor.track_grid_from_svg(args.calibration_svg, args.grid_size)
    map_point = unwarp.scipy_interpolate_fit(grid_data, args.grid_size)

    print('calculating coordinate map')
    return unwarp.calculate_coordinate_map(map_point, args.grid_size, args.output_pixels_per_grid_unit)


def process_image(f: Path, args):
    global _unwarp_params
    output_extension = args.output_format if args.output_format[0] == '.' else '.' + args.output_format

    if args.destination_folder is not None:
        args.destination_folder.mkdir(exist_ok=True)
        filename_convert = lambda p: args.destination_folder.joinpath(p.stem + output_extension)
    else:
        filename_convert = lambda p: p.parent.joinpath('unwarped_' + p.stem + output_extension)

    output_path = filename_convert(f)
    assert output_path != f  # make sure we don't overwrite the original
    print(f'{f} -> {output_path}')
    unwarp.unwarp_image(f, output_path, *_unwarp_params)
    return 1


from itertools import repeat

if platform.system() == "Windows":
    def init_pool(unwarp_params):
        global _unwarp_params
        _unwarp_params = unwarp_params


@exec_timer.timeit
def process_all_images(args, unwarp_params):
    global _unwarp_params
    _unwarp_params = unwarp_params
    if platform.system() == "Windows":
        with multiprocessing.Pool(processes=args.processes if args.processes > 0 else None, initializer=init_pool, initargs=(_unwarp_params,)) as p:
            return sum(p.starmap(process_image, zip(args.input_files, repeat(args))))
    else:
        with multiprocessing.Pool(processes=args.processes if args.processes > 0 else None) as p:
            return sum(p.starmap(process_image, zip(args.input_files, repeat(args))))

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument('--destination-folder', '-d', type=Path, help='If set, original filenames are used. Else the files are stored in the current directory with the prefix "unwarped"')
    argparser.add_argument('--output-format', default='png', help='jpg, png, tiff, etc ... Can be any format supported by imageio')
    argparser.add_argument('--processes', default=-1, type=int, help='Number of simultaneous processes. Default equals amount of CPU cores')
    argparser.add_argument('calibration_svg')
    argparser.add_argument('grid_size_x', type=int)
    argparser.add_argument('grid_size_y', type=int)
    argparser.add_argument('output_pixels_per_grid_unit', type=int)
    argparser.add_argument('input_files', nargs='*', type=lambda x: list(map(Path, glob(x))))

    args = argparser.parse_args()
    args.grid_size = (args.grid_size_y, args.grid_size_x)

    args.input_files = list(flatten(args.input_files))

    unwarp_params = prepare_coordinate_map(args)

    no_processed_images = process_all_images(args, unwarp_params)
    preperation_time = exec_timer.logtime_data["prepare_coordinate_map"]["total_time"]
    unwarping_time = exec_timer.logtime_data["process_all_images"]["total_time"]
    print('Statistics:')
    print(f'\tNumber of processed pictures: {no_processed_images}')
    print(f'\tPreperation time: {preperation_time/1000:.2f}s')
    print(f'\tUnwarping time:  {unwarping_time/1000:.2f}s ({unwarping_time/no_processed_images:.0f}ms per image)')
