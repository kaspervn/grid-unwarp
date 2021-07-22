import argparse

import grid_extractor
import unwarp

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-b', '--background-image')
    argparser.add_argument('calibration_svg')
    argparser.add_argument('grid_size_x', type=int)
    argparser.add_argument('grid_size_y', type=int)

    args = argparser.parse_args()

    grid_size = (args.grid_size_y, args.grid_size_x)

    grid_rows = grid_extractor.track_grid_from_svg(args.calibration_svg, grid_size)

    # map_point = single_poly_fit(grid_rows, grid_size, 5)
    map_point = unwarp.scipy_interpolate_fit(grid_rows, grid_size)
    unwarp.diagnostic_draw(map_point, grid_size, grid_rows, args.background_image)
