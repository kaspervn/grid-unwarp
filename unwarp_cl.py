import pyopencl as cl
import argparse
from pathlib import Path
from glob import glob

from imageio import imread, imwrite
from more_itertools import flatten
import numpy as np
import joblib

from execution_time import ExecutionTime

import grid_extractor
import unwarp

import os.path

exec_timer = ExecutionTime()

@exec_timer.timeit
def prepare_coordinate_map(calibration_svg, grid_size, output_pixels_per_grid_unit):
    print('determining grid lines')
    grid_data = grid_extractor.track_grid_from_svg(calibration_svg, grid_size)
    map_point = unwarp.scipy_interpolate_fit(grid_data, grid_size)

    print('calculating coordinate map')
    return unwarp.calculate_coordinate_map(map_point, grid_size, output_pixels_per_grid_unit)


def output_filename_func(args):
    output_extension = args.output_format if args.output_format[0] == '.' else '.' + args.output_format

    if args.destination_folder is not None:
        args.destination_folder.mkdir(exist_ok=True)
        filename_convert = lambda p: args.destination_folder.joinpath(p.stem + output_extension)
    else:
        filename_convert = lambda p: p.parent.joinpath('unwarped_' + p.stem + output_extension)
    return filename_convert


@exec_timer.timeit
def process_all_images(args, output_size, x_coordinates, y_coordinates):
    filename_conv_func = output_filename_func(args)
    ctx = cl.create_some_context(False)
    print(ctx)

    with open(os.path.join(os.path.dirname(__file__), 'map_coordinates.cl')) as f:
        kernel = cl.Program(ctx, f.read()).build().map_coordinates

    queue = cl.CommandQueue(ctx)

    x_coordinates = np.array(x_coordinates, dtype=np.float32).reshape(output_size)
    y_coordinates = np.array(y_coordinates, dtype=np.float32).reshape(output_size)

    x_map_clbuf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=x_coordinates)
    y_map_clbuf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=y_coordinates)
    output_npbuf = np.zeros(output_size, dtype=np.uint8)
    output_clbuf = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, output_size[0] * output_size[1])

    for n, f in enumerate(args.input_files):
        img = imread(f)
        assert img.dtype == np.uint8

        # cl.enqueue_copy(queue, input_clbuf, np.reshape(img, (img.size)))
        input_clbuf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=img)
        kernel(queue, output_size, None, input_clbuf, x_map_clbuf, y_map_clbuf, output_clbuf, np.uint64(img.shape[1]))
        cl.enqueue_copy(queue, output_npbuf, output_clbuf).wait()

        output_path = filename_conv_func(f)
        assert output_path != f  # make sure we don't overwrite the original
        print(f'{f} -> {output_path}')
        imwrite(output_path, output_npbuf)
        input_clbuf.release()

    queue.flush()
    queue.finish()

    return len(args.input_files)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument('--destination-folder', '-d', type=Path, help='If set, original filenames are used. Else the files are stored in the current directory with the prefix "unwarped"')
    argparser.add_argument('--output-format', default='png', help='jpg, png, tiff, etc ... Can be any format supported by imageio')
    argparser.add_argument('calibration_svg')
    argparser.add_argument('grid_size_x', type=int)
    argparser.add_argument('grid_size_y', type=int)
    argparser.add_argument('output_pixels_per_grid_unit', type=int)
    argparser.add_argument('input_files', nargs='*', type=lambda x: list(map(Path, glob(x))))

    args = argparser.parse_args()
    args.grid_size = (args.grid_size_y, args.grid_size_x)

    args.input_files = list(flatten(args.input_files))

    cache = joblib.Memory('.')
    prepare_coordinate_map = cache.cache(prepare_coordinate_map)
    unwarp_params = prepare_coordinate_map(args.calibration_svg, args.grid_size, args.output_pixels_per_grid_unit)

    no_processed_images = process_all_images(args, *unwarp_params)
    if prepare_coordinate_map in exec_timer.logtime_data:
        preperation_time = exec_timer.logtime_data["prepare_coordinate_map"]["total_time"]
    else:
        preperation_time = 0

    unwarping_time = exec_timer.logtime_data["process_all_images"]["total_time"]
    print('Statistics:')
    print(f'\tNumber of processed pictures: {no_processed_images}')
    print(f'\tPreperation time: {preperation_time/1000:.2f}s')
    print(f'\tUnwarping time:  {unwarping_time/1000:.2f}s ({unwarping_time/no_processed_images:.0f}ms per image)')
