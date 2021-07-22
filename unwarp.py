from itertools import product

import matplotlib.pyplot as plt
import numpy as np
import numpy.linalg
import scipy.interpolate
import scipy.ndimage
from imageio import imread, imwrite


import grid_extractor


def single_poly_fit(grid_rows, grid_size, order):
    def polynomial_2D_terms(order):
        return list(product(range(order + 1), range(order + 1)))[:-1]

    poly_terms = polynomial_2D_terms(order)

    yx_pairs = list(product(range(grid_size[0]), range(grid_size[1])))


    target_grid_point_map = lambda y, x: (float(y), float(x))
    source_grid_point_map = lambda y, x: grid_rows[y][x][0]

    mat_row = lambda x, y: np.array([x**xn * y**yn for xn, yn in poly_terms])
    a = np.vstack([mat_row(*target_grid_point_map(x, y)) for x, y in yx_pairs])
    b_fory = np.array([source_grid_point_map(y, x)[0] for y, x in yx_pairs])
    b_forx = np.array([source_grid_point_map(y, x)[1] for y, x in yx_pairs])

    y_params = np.linalg.lstsq(a, b_fory, rcond=False)[0]
    x_params = np.linalg.lstsq(a, b_forx, rcond=False)[0]

    poly_eval = lambda y, x, c: sum([cn * x**xn * y**yn for cn, (xn, yn) in zip(c, poly_terms)])

    map_point = lambda y, x: np.array([poly_eval(y, x, y_params), poly_eval(y, x, x_params)])

    return map_point


def scipy_interpolate_fit(grid_rows, grid_size):

    grid_data_y = np.array([[x[0][0] for x in row] for row in grid_rows])
    grid_data_x = np.array([[x[0][1] for x in row] for row in grid_rows])

    y_func = scipy.interpolate.RectBivariateSpline(np.arange(grid_size[0]), np.arange(grid_size[1]), grid_data_y)
    x_func = scipy.interpolate.RectBivariateSpline(np.arange(grid_size[0]), np.arange(grid_size[1]), grid_data_x)

    return lambda y, x: np.array([y_func.ev(y, x), x_func.ev(y, x)])


def diagnostic_draw(map_point, grid_size, grid_rows, background_img=None, plot_input_grid=True):

    points = [map_point(y, x) for y, x in product(np.arange(grid_size[0] - 0.5, step=0.5),
                                                  np.arange(grid_size[1] - 0.5, step=0.5))]
    fig, ax = plt.subplots()
    if background_img is not None:
        img = plt.imread(background_img)
        plt.imshow(img, cmap='gray')
        ax.set(ylim=(img.shape[0], 0), xlim=(0, img.shape[1]))

    ax.plot([p[1] for p in points], [p[0] for p in points], 'x', color='red')
    if plot_input_grid:
        grid_extractor.plot_grid(grid_rows, grid_size, None, False, ax)
    plt.tight_layout()
    plt.show()


def calculate_coordinate_map(map_point_func, grid_size, pixels_per_grid_unit: int):
    assert type(pixels_per_grid_unit) == int
    output_size = pixels_per_grid_unit * (np.array(grid_size) - 1)

    coordinate_iter = lambda: (p / pixels_per_grid_unit for p in map(np.array, product(range(output_size[0]), range(output_size[1]))))

    y_coordinates = [map_point_func(*(p))[0] for p in coordinate_iter()]
    x_coordinates = [map_point_func(*(p))[1] for p in coordinate_iter()]

    return output_size, x_coordinates, y_coordinates


def unwarp_image(img_path, output_img_path, output_size, x_coordinates, y_coordinates):
    img = imread(img_path)
    if len(img.shape) == 2:
        result = scipy.ndimage.map_coordinates(img, [y_coordinates, x_coordinates], order=1).view()
        result.shape = (output_size[0], output_size[1])
    elif len(img.shape) == 3:
        no_channels = img.shape[2]
        result = np.zeros((output_size[0], output_size[1], no_channels), dtype=np.uint8)
        for channel in range(no_channels):
            result[...,channel] = scipy.ndimage.map_coordinates(img[...,channel], [y_coordinates, x_coordinates], order=1).reshape(output_size[1], output_size[0])
    imwrite(output_img_path, result)


def unwarp_images(img_paths, map_point_func, grid_size, pixels_per_grid_unit, map_target_filename):
    output_size, x_coordinates, y_coordinates = calculate_coordinate_map(map_point_func, grid_size, pixels_per_grid_unit)

    for img_path in img_paths:
        unwarp_image(img_path, map_target_filename(img_path), output_size, x_coordinates, y_coordinates)

# some testing code to debug
if __name__ == '__main__':
    grid_size = (25, 23)
    grid_data = grid_extractor.track_grid_from_svg('example.svg', grid_size)
    map_point = scipy_interpolate_fit(grid_data, grid_size)

    unwarp_images(['example.png'], map_point, grid_size, 10, lambda p: 'unwarped_' + p)
