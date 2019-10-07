import sys

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

class PathNotFoundException(Exception):
    pass


class PathNotInAbsoluteCoordinatesException(Exception):
    pass


def line_contains_path_string(line):
    return line.lstrip()[:3] == 'd="'


def find_path_string(filename):
    """
    Search for the line in the svg-file that describes the path. It is of the
    form
                d="M 1.2,2.3 C 3.4,4.5 5.6,6.7 7.8,8.9 C  ...  "
    and so the function looks for lines that start with 'd="'.
    
    arg: filename - name of svg-file
    ret: path string
    """
    with open(filename) as f:
        line = f.readline()
        while line:
            if line_contains_path_string(line): 
                return line.lstrip()
            line = f.readline()
    raise PathNotFoundException()


def extract_control_points(path_string_words):
    """
    arg: path_string_words
                These are the words of the path string, which are either path types,
                        'M', 'L', 'S', 'C'
                or coordinate pairs in string form.

    returns: control_points
                A list containing all information needed to make each curve individually,
                e.g.
                        [...
                         ['C', 'x1,y1', 'x2,y2', 'x3,y3'],
                         ['L', 'x1,y1'],
                         ...]
                The first control point 'x0,y0' is always the last control point of the
                previous curve.
    """
    curve_type = path_string_words.pop(0)
    P_start = path_string_words.pop(0)
    control_points = [[curve_type, P_start]]

    while len(path_string_words) != 0:
        if len(path_string_words[0]) == 1:
            curve_type = path_string_words.pop(0)
        else:
            if curve_type in ['M', 'L']:
                P1 = path_string_words.pop(0)
                control_points.append(['L', P1])
            elif curve_type == 'S':
                P1 = path_string_words.pop(0)
                P2 = path_string_words.pop(0)
                control_points.append([curve_type, P1, P2])
            elif curve_type == 'C':
                P1 = path_string_words.pop(0)
                P2 = path_string_words.pop(0)
                P3 = path_string_words.pop(0)
                control_points.append([curve_type, P1, P2, P3])
            elif curve_type in ['m', 'l', 's', 'c']:
                raise PathNotInAbsoluteCoordinatesException()
            else:
                raise Exception
    return control_points


def bezier_points_from_svg_curves(curve_list):
    """
    arg: curve_list
                A list of curve information in string form, as returned by the function
                above.

    returns: bez_points
                A list with both type of curve and its control points in np.array-form,
                ready to be used in calculations.
                The type of Bezier-curve is always either
                    'M' - Starting point (one point)
                    'L' - Linear (two points)
                    'C' - Cubic spline (four points)
    """
    assert curve_list[0][0] == 'M'
    bez_points = [] # contains elements ['char', (x,y), ... ]
    curve_type = 'M'
    for curve in curve_list:
        if curve[0] == 'M':
            start_point = np.array(eval(curve[1]))
            bez_points.append(['M', start_point])
        elif curve[0] == 'L':
            P0 = bez_points[-1][-1]
            P1 = np.array(eval(curve[1]))
            bez_points.append(['L', P0, P1])
        elif curve[0] == 'S':
            P0 = bez_points[-1][-1]
            P1 = 2 * P0 - bez_points[-1][-2]
            P2 = np.array(eval(curve[1]))
            P3 = np.array(eval(curve[2]))
            bez_points.append(['C', P0, P1, P2, P3])
        elif curve[0] == 'C':
            P0 = bez_points[-1][-1]
            P1 = np.array(eval(curve[1]))
            P2 = np.array(eval(curve[2]))
            P3 = np.array(eval(curve[3]))
            bez_points.append(['C', P0, P1, P2, P3])
    return bez_points


def cubic(t, P0, P1, P2, P3):
    return (P0 * (1-t)**3 + P1 * 3 * (1-t)**2 * t + P2 * 3 * (1-t) * t**2 + P3 * t**3)


def linear(t, P0, P1):
    return (P0 * (1-t) + P1 * t)
    

class Bezier:
    def __init__(self):
        self.points = []
        self.curve_type = []

    def __call__(self, x):
        n = int(x * len(self.points)) % len(self.points)
        t = (x * len(self.points)) % 1
        if self.curve_type[n] == 'L':
            return linear(t, *self.points[n])
        elif self.curve_type[n] == 'C':
            return cubic(t, *self.points[n])
        else:
            raise Exception

    def add_curve(self, curve):
        self.curve_type.append(curve[0])
        self.points.append(curve[1:])


def x_y_from_svg(filename):
    """
    Builds a list of points on the curve taken from the svg-file in filename.

    Each Bezier-curve is sampled at 100-points, equidistant in the parameter t.
    """
    path_string = find_path_string(filename)[3:-2]
    path_string_words = path_string.split()
    control_points = extract_control_points(path_string_words)
    bezier_points = bezier_points_from_svg_curves(control_points)
    mybez = Bezier()
    for bezier in bezier_points[1:]: # Skip starting point (M, (x,y))
        mybez.add_curve(bezier)

    resolution = 100 * len(bezier_points)
    points = [mybez(t/resolution) for t in range(resolution)]
    x = [p[0] for p in points]
    y = [-p[1] for p in points]
    return x, y

