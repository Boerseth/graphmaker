import sys

import numpy as np
import matplotlib.pyplot as plt
import imageio
from PIL import Image


"""
================================================================================
        F I N D   C U R V E   F R O M   J P G
================================================================================
"""

class CannotFindOutlineException(Exception):
    pass


class Walker:
    """
    Take a landscape with a binary `height`, and walk along its border.

    Its two feet locations must be on separate sides of the border, placed
    on either the same `x` or the same `y` coordinate at all times.

    Steps
    are made in lengths as big as the spread of the initial positions of
    the feet.
    
    Turns are always right angled.
    """
    def __init__(self, height, left_foot, right_foot):
        self.height = height
        
        self.left_foot = left_foot
        self.right_foot = right_foot
        self.left_start = left_foot
        self.right_start = right_foot

        spread = self.right_foot - self.left_foot
        self.forward = np.array([-spread[1], spread[0]])
        self.R_matrix = np.array([[0,1],[-1,0]]) # Rotation, pi/2 clockwise

        self.has_returned = False
        
        assert spread[0] == 0 or spread[1] == 0
        assert height(self.left_foot) != height(self.right_foot)

    def get_feet_positions(self):
        return [self.left_foot, self.right_foot]
    
    def get_midpoint(self):
        return [(self.left_foot[0] + self.right_foot[0])/2,
                (self.left_foot[1] + self.right_foot[1])/2]

    def make_step(self):
        if self.can_step_forth():
            self.step_forth()
        else:
            self.turn()
        self.check_if_returned()

    def can_step_forth(self):
        return self.left_foot_can_step() and self.right_foot_can_step()

    def left_foot_can_step(self):
        return (self.height(self.left_foot) == self.height(self.left_foot + self.forward))

    def right_foot_can_step(self):
        return (self.height(self.right_foot) == self.height(self.right_foot + self.forward))

    def step_forth(self):
        self.left_foot = self.left_foot + self.forward
        self.right_foot = self.right_foot + self.forward

    """
    Turning right is the default, since the assumed walking direction is clockwise.
    In the event that the edge touches itself at a pixel, e.g. like
    
                ######
                ##  ##
                  ####
                 ^^
    the walker turns right and walks along the peninsula's coast, and continues past 
    the touching pixels onward to the left when it returns to the mainland.
    """
    def turn(self):
        if self.must_turn_right():
            self.turn_right()
        else:
            self.turn_left()

    def must_turn_right(self):
        return (self.height(self.right_foot + self.forward) == self.height(self.left_foot))
    
    def turn_right(self):
        self.left_foot = self.right_foot + self.forward
        self.forward = self.R_matrix.dot(self.forward)

    def turn_left(self):
        self.right_foot = self.left_foot + self.forward
        self.forward = - self.R_matrix.dot(self.forward)

    def check_if_returned(self):
        left_returned = np.allclose(self.left_foot, self.left_start)
        right_returned = np.allclose(self.right_foot, self.right_start)
        self.has_returned = self.has_returned or (left_returned and right_returned)


def find_first_diagonal_point_with_height_change(height, size):
    diag = 1
    while height([diag, diag]) == height([0,0]):
        diag += 1
        if diag > size-1:
            raise CannotFindOutlineException()
    return diag


def clockwise_moving_starting_pair(height, diag):
    outer_height = height([0,0])
    diagonal_point = [diag, diag]
    diagonal_point_prev = [diag-1, diag-1]
    neighbour_point = [diag-1, diag]
    if height(neighbour_point) == outer_height:
        return (np.array(neighbour_point), np.array(diagonal_point))
    else:
        return (np.array(diagonal_point_prev), np.array(neighbour_point))


def find_starting_point(height, size):
    diag = find_first_diagonal_point_with_height_change(height, size)
    return clockwise_moving_starting_pair(height, diag)


def find_edge(height, size):
    starting_point = find_starting_point(height, size)
    walker = Walker(height, *starting_point)
    edge = [walker.get_midpoint()]
    while not walker.has_returned:
        walker.make_step()
        edge.append(walker.get_midpoint())
    return edge


def pixel_to_binary(pixel_value):
    if pixel_value >= 128:
        return 1
    else:
        return 0


def get_edge_from_image(filename):
    im = Image.open(filename).rotate(270)
    im_array = np.array(im)
    N,M = len(im_array[:,0]), len(im_array[0,:])
    im_list = [[pixel_to_binary(im_array[n,m,0]) for m in range(M)]
                                                    for n in range(N)]
    height = lambda v: im_list[v[0]][v[1]]
    size = max(N, M)
    return find_edge(height, size)


def cartesian_from_tuple_list(tuple_list):
    x = [e[0] for e in tuple_list]
    y = [e[1] for e in tuple_list]
    return x, y


def x_y_from_png(filename):
    edge = get_edge_from_image(filename)
    x, y = cartesian_from_tuple_list(edge)
    return x, y


"""
================================================================================
        F I N D   C U R V E   F R O M   S V G
================================================================================
"""
class PathNotFoundException(Exception):
    pass


class PathNotInAbsoluteCoordinatesException(Exception):
    pass


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
            if line.lstrip()[:3] == 'd="': # Path string starts with 'd="'
                return line.lstrip()
            line = f.readline()
    raise PathNotFoundException()


def extract_control_points(path_string_words):
    """
    arg: path_string_words
                These are the words of the path string, which are either path types,
                        'M', 'L', 'S', 'C'
                or coordinate pairs in string form.

    returns: curves
                A list containing all information needed to make each curve individually,
                e.g.
                        [...
                         ['C', 'x1,y1', 'x2,y2', 'x3,y3'],
                         ['L', 'x1,y1'],
                         ...]
                The first control point 'x0,y0' is always the last control point of the
                previous curve.
    """
    control_points = []
    curve_type = 'M'
    while len(path_string_words) != 0:
        if len(path_string_words[0]) == 1:
            curve_type = path_string_words.pop(0)
        else:
            if curve_type in ['M', 'L']:
                P1 = path_string_words.pop(0)
                control_points.append([curve_type, P1])
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


"""
================================================================================
        F O U R I E R
================================================================================
"""
class Fourier_matrix:
    def __init__(self, N, M):
        self.N = N
        self.M = M
        self.COS = np.array([[np.cos(n * m * 2 * np.pi / M) 
            for m in range(M)]
            for n in range(1, N+1)])
        self.SIN = np.array([[np.sin(n * m * 2 * np.pi / M) 
            for m in range(M)]
            for n in range(1, N+1)])
        self.COST = self.COS.T
        self.SINT = self.SIN.T
    
    def make_coeffs(self, f):
        a = self.COS.dot(f) / self.M # Integral, divide by M to normalise
        b = self.SIN.dot(f) / self.M
        return a, b

    def make_approximation(self, a, b, n):
        if n >= self.N:
            return self.COST.dot(a) + self.SINT.dot(b)
        else:
            siev = np.array([1.0]*n + [0.0]*(self.N - n))
            a_sieved = a * siev
            b_sieved = b * siev
            return self.COST.dot(a_sieved) + self.SINT.dot(b_sieved)

    def make_smooth_approximation(self, a, b, n_continuous):
        if n_continuous >= self.N:
            siev = np.array([1.0]*self.N)
        elif n_continuous < 0:
            siev = np.array([0.0]*self.N)
        else:
            n = int(n_continuous)
            t = n_continuous % 1
            siev = np.array([1.0]*n + [t] + [0.0]*(self.N - n - 1))
        a_sieved = a * siev
        b_sieved = b * siev
        return self.COST.dot(a_sieved) + self.SINT.dot(b_sieved)





"""
================================================================================
        L a T e X
================================================================================
"""
def decimals_and_power(number):
    log_10_number = np.log(abs(number)) / np.log(10)
    power = str(int(log_10_number // 1))
    decimals = str(10**(log_10_number % 1))
    sign = "" if (np.sign(number) > 0) else "-"
    return decimals, power, sign


def number_to_scientific_latex(number):
    if number == 0:
        return "0"
    decimals, power, sign = decimals_and_power(number)
    ret_string = sign
    ret_string += decimals[:min(6, len(decimals))]
    if power != "0" and power != "1":
        ret_string += " \\cdot 10^{{ {} }}".format(power)
    elif power == 1:
        ret_string += " \\cdot 10"
    return ret_string


"""
The separator is surprisingly intricate. Here is the justification:

I want there to be a comma and ampersand between each coefficient,
        ... a_n &= 1.23   , &    a_n+1 &= 4.56   , &   ...
                           ^                      ^
But there must not be any `&` after the `last` coefficient of a line.

Also, if the `final` line of coefficients does not fill all collumns,
say for the case of 3 columns and 4 coefficients,
        a_1 &= 1.2  , &  a_2 &= 3.4  , &  a_3 &= 5.6 \\
        a_4 &= 7.8  , &&&& \\
the trailing ampersands must still be included.

Finally, every line must be ended by a newline, _except_ if it is the
final line of the `d`-coefficients.
        d_1 &= 1.2  , &  d_2 &= 3.4  , &  d_3 &= 5.6 \\
        d_4 &= 7.8  , &&&&
        \end{align*}
"""
def separator(n, N, n_cols, letter):
    is_final = (n == N-1)
    is_last = (n % n_cols == n_cols-1)
    is_d = (letter == 'd')

    if is_last:
        if is_final and is_d:
            return " \n"
        else:
            return ",\\\\ \n"
    else:
        if is_final:
            trailing_ampersands = "&"*(2*(n_cols - 1 - (n%n_cols)))
            ret_string = ""
            ret_string += " " if is_d else ", "
            ret_string += trailing_ampersands
            ret_string += " \n" if is_d else " \\\\ \n"
            return ret_string
        else:
            return ", & "
    

def latex_simplified_formula(a,b,c,d,n_cols):
    assert len(a) == len(b) and len(a) == len(c) and len(a) == len(d)
    N = len(a)
    begin_align = "\\begin{align*}\n"
    end_align =  "\\end{align*}\n"
    empty_line = "&"*(2*n_cols - 1) + " \\\\ \n"
    
    ret_string = ""
    ret_string += begin_align
    ret_string += "x(t) &= \\sum\\limits_{{n=1}}^{{ {} }} ".format(N)
    ret_string += "\\Big[a_n \\cos(2n\\pi t) + b_n \\sin(2n\\pi t) \\Big]\\\\ \n"
    ret_string += "y(t) &= \\sum\\limits_{{n=1}}^{{ {} }} ".format(N)
    ret_string += "\\Big[c_n \\cos(2n\\pi t) + d_n \\sin(2n\\pi t) \\Big]\n"
    ret_string += end_align
    ret_string += "\n"

    ret_string += begin_align
    for letter, coeff_list in [('a', a), ('b', b), ('c', c), ('d', d)]:
        for n in range(N):
            ret_string += "{}_{{ {} }} &= ".format(letter, n+1)
            ret_string += number_to_scientific_latex(coeff_list[n])
            
            ret_string += separator(n, N, n_cols, letter)
        if letter != 'd':
            ret_string += empty_line
    ret_string += end_align
    return ret_string
    

def latex_complete_formula(a,b,c,d,n_cols, n_rows):
    N = len(a)
    assert len(b) == N
    assert len(c) == N
    assert len(d) == N
    
    begin_align = "\\begin{align*}\n"
    end_align =  "\\end{align*}\n"
    empty_line = "& \\\\ \n"

    ret_string = begin_align
    ret_string += "  t \\in \\mathbb{R}\n"
    ret_string += end_align
    ret_string += "\n"

    visual_row_count = 3  # Not used for anything yet...

    ret_string += begin_align
    ret_string += "  x(t) &= "
    for n in range(N):
        if (n % n_cols == 0) and (n > 0):
            ret_string += "& "
        if (n > 0) and (a[n] > 0):
            ret_string += "+ "
        # cosine
        ret_string += number_to_scientific_latex(a[n])
        ret_string += " \\cos ( {} \\cdot 2 \\pi t ) ".format(n + 1)

        # sine
        if (b[n] > 0):
            ret_string += "+ "
        ret_string += number_to_scientific_latex(b[n])
        ret_string += " \\sin ( {} \\cdot 2 \\pi t ) ".format(n + 1)
        
        if (n == N-1) or (n % n_cols == n_cols-1):
            ret_string += "\\\\ \n  "
            visual_row_count += 1

    ret_string += empty_line

    ret_string += "y(t) &= "
    for n in range(N):
        if (n % n_cols == 0) and (n > 0):
            ret_string += "& "
        if (n > 0) and (c[n] > 0):
            ret_string += "+ "
        # cosine
        ret_string += number_to_scientific_latex(c[n])
        ret_string += " \\cos ( {} \\cdot 2 \\pi t ) ".format(n + 1)

        # sine
        if (d[n] > 0):
            ret_string += "+ "
        ret_string += number_to_scientific_latex(d[n])
        ret_string += " \\sin ( {} \\cdot 2 \\pi t ) ".format(n + 1)
        
        if (n == N-1):
            ret_string += " \n"
            visual_row_count += 1
        elif (n % n_cols == n_cols-1):
            ret_string += "\\\\ \n  "
            visual_row_count += 1
                
    ret_string += end_align
    return ret_string


"""
================================================================================
        M  A  I  N
================================================================================
"""
if __name__ == "__main__":
    
    filepath = sys.argv[1]
    filetype = filepath[-3:]
    if filetype == 'svg':
        x, y = x_y_from_svg(filepath)
    elif filetype == 'png':
        x, y = x_y_from_png(filepath)
    else:
        print('File format not recognised!')
        print('Rename file (.svg, .png), or convert to the correct format and try again.')
    
    N = eval(sys.argv[2])
    M = len(x) # == len(y)

    x = np.array(x)
    y = np.array(y)
    x = x - sum(x)/M
    y = y - sum(y)/M

    x_scope = (min(x)-20, max(x)+20)
    y_scope = (min(y)-20, max(y)+20)
    scope = (min(min(x), min(y)) - 20,
             max(max(x), max(y)) + 20)

    my_fo = Fourier_matrix(N, M)
    a, b = my_fo.make_coeffs(x)
    c, d = my_fo.make_coeffs(y)

    x_appr = my_fo.make_approximation(a, b, N)
    y_appr = my_fo.make_approximation(c, d, N)

    # Make plot
    plt.figure(figsize=(20,15))
    plt.axis("equal")
    plt.plot(list(x_appr), list(y_appr))
    figurename = "{}.jpg".format(filepath[:-4])
    plt.savefig(figurename)
    #plt.close()
    
    latex_simplified = latex_simplified_formula(a,b,c,d,4)
    latex_complete = latex_complete_formula(a,b,c,d,2, 10)

    with open('lsimp.tex', 'w') as f:
        f.write(latex_simplified)

    with open('lcomp.tex', 'w') as f:
        f.write(latex_complete)
