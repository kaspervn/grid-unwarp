# Grid unwarp #
Software to unwarp images based on a grid calibration image. The calibration can be done by providing a svg file made with a vector program (Inkscape for example) with dots on the grid intersection points.

![alt text](demonstration.png "demonstration")

## Usage ##
There are two tools: `test_grid.py` and `unwarp_batch.py`. 

* `test_grid.py` lets you generate a  test image to check if the grid is detected correctly (the continous lines) and if the interpolation works (shown by the red crosses). To check the usage see `test_grid.py --help` 

* `unwarp_batch.py` lets you unwarp one or many images based on the same calibration data. See `unwarp_batch.py --help`

## Examples ##
- run `python test_grid.py -b example.png example.svg 23 25` to show a test image applied to the example image
- run `python unwarp_batch.py --output-format=jpg example.svg 23 25 20 example.png`


## Creating calibration images ##
- The objects at the intersections should be circles
- All the circles should have color magenta (`#FF00FF`) except for the special types
- The upper left corner is marked by a green dot (`#00FF00`)
- The second dot on the first row should be red (`#FF0000`)
- The second dot on the first column should be blue (`#0000FF`)
- The grid should be rectangular
- The units of the file should be in pixels
- The svg file should have the same dimensions as the to be processed images
- Check the grid by running `test_grid.py`


## Requirements
- Python 3.7 or higher
- numpy
- imageio
- scipy.ndimage
- scipy.interpolate
- matplotlib (for `test_grid.py`)
