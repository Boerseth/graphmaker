import sys

import numpy as np
import matplotlib.pyplot as plt
import imageio


"""
================================================================================
        F I N D   C U R V E   F R O M   J P G
================================================================================
"""
# TODO: Paste in this piece of code


"""
================================================================================
        F I N D   C U R V E   F R O M   S V G
================================================================================
"""
def find_path_string(filepath):
    with open(filepath) as fp:
        line = fp.readline()
        cnt = 1
        while line:
            if line.lstrip()[:3] == 'd="': # Look for the path string, which starts with 'd="'
                return line.lstrip()
            line = fp.readline()
            cnt += 1


def curves_from_coords(coords):
    """
    arg: coords
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
    curves = []
    curve_type = 'M'
    while len(coords) != 0:
        if len(coords[0]) == 1:
            curve_type = coords.pop(0)
        else:
            if curve_type in ['m', 'M','l', 'L']:
                curves.append([curve_type, coords.pop(0)])
            elif curve_type in ['s', 'S']:
                curves.append([curve_type, coords.pop(0), coords.pop(0)])
            elif curve_type in ['c', 'C']:
                curves.append([curve_type, coords.pop(0), coords.pop(0), coords.pop(0)])
            else:
                raise Exception
    return curves


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
    line = find_path_string(filename)[3:-2]
    linelist = line.split()
    curves = curves_from_coords(linelist)
    bezier_points = bezier_points_from_svg_curves(curves)
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
        self.SIN = np.array([[np.sin(n * m * 2* np.pi / M) 
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

print(number_to_scientific_latex(np.pi*10000))


def separator(n, N, n_cols, letter):
    is_final = (n == N-1)
    is_last = (n % n_cols == n_cols-1)
    is_d = (letter == 'd')

    if is_last:
        if is_final and is_d:
            return ", \n"
        else:
            return ",\\\\ \n"
    else:
        if is_final:
            ampersands = "&"*(2*(n_cols - 1 - (n%n_cols)))
            if is_d:
                return " " + ampersands + " \n"
            else:
                return ", " + ampersands + " \\\\ \n"
        else:
            return ", & "
    

def latex_simplified_formula(a,b,c,d,n_cols):
    assert len(a) == len(b) and len(a) == len(c) and len(a) == len(d)
    N = len(a)
    ret_string = ""
    ret_string += "\\begin{align*}\n"
    ret_string += "x(t) &= \\sum\\limits_{{n=1}}^{{ {} }} \\Big[ a_n \\cos(2n\\pi t) + b_n \\sin(2n\\pi t) \\Big] \\\\ \n".format(N)
    ret_string += "y(t) &= \\sum\\limits_{{n=1}}^{{ {} }} \\Big[ c_n \\cos(2n\\pi t) + d_n \\sin(2n\\pi t) \\Big] \n".format(N)
    ret_string += "\\end{align*}\n"
    ret_string += "\n"

    ret_string += "\\begin{align*}\n"
    for letter, coeff_list in [('a', a), ('b', b), ('c', c), ('d', d)]:
        for n in range(N):
            ret_string += "{}_{{ {} }} &= ".format(letter, n+1)
            ret_string += number_to_scientific_latex(coeff_list[n])
            
            ret_string += separator(n, N, n_cols, letter)
        if letter != 'd':
            ret_string += "&"*(2*n_cols - 1) + " \\\\ \n"
    ret_string += "\\end{align*}\n"
    return ret_string
    

def latex_complete_formula(a,b,c,d,n_cols, n_rows):
    N = len(a)
    assert len(b) == N
    assert len(c) == N
    assert len(d) == N

    ret_string = "\\begin{align*}\n"
    ret_string += "  t \\in \\mathbb{R}\n"
    ret_string += "\\end{align*}\n"
    ret_string += "\n"

    visual_row_count = 3

    ret_string += "\\begin{align*}\n"
    
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

    ret_string += "& \\\\ \n"

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
        
        if (n == N-1) or (n % n_cols == n_cols-1):
            if not (n == N-1):
                ret_string += "\\\\ \n  "
                visual_row_count += 1
            else:
                ret_string += " \n"
                visual_row_count += 1
    ret_string += "\\end{align*}\n"
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
    elif filetype in ['jpg', 'jpeg']:
        x, y = x_y_from_jpg(filepath)
    
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
    plt.figure(figsize=(15,15))
    plt.axis((*x_scope, *y_scope))
    plt.axis("scaled")
    plt.plot(x_appr, y_appr)
    figurename = "{}.jpg".format(filepath[:-4])
    plt.savefig(figurename)
    plt.close()
    
    latex_simplified = latex_simplified_formula(a,b,c,d,4)
    latex_complete = latex_complete_formula(a,b,c,d,2, 10)

    with open('lsimp.tex', 'w') as f:
        f.write(latex_simplified)

    with open('lcomp.tex', 'w') as f:
        f.write(latex_complete)
