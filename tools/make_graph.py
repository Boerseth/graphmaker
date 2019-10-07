import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt

from .fourier_matrix import Fourier_matrix
from .path_finder_svg import x_y_from_svg
from .path_finder_png import x_y_from_png
from .tex_maker import latex_complete_formula, latex_simplified_formula, latex_old_simplified_formula



def too_large_order_error_message(N, M):
    rows, cols = os.popen('stty size', 'r').read().split()
    print('\n{0:{fill}{align}{width}}'.format('', fill='-', align='^', width=cols));
    print('{0:{fill}{align}{width}}'.format(' Error ', fill='=', align='^', width=cols));
    print('The decired order is too large for the number of measurement points!')
    print('\t(N = {} > M = {})'.format(N, M))
    print('Either use a larger scale, or lower the order.')
    print('{0:{fill}{align}{width}}'.format('', fill='-', align='^', width=cols));
    print('\n(using N = {})'.format(M))


def spline_maker(points):
    T = len(points)
    def f(t):
        n = int(t*T) % T
        q = (t*T) % 1
        return points[n] * (1-q) + points[(n+1)%T] * q
    return f


def sampler(f, M):
    sample = [f(m/M) for m in range(M)]
    return sample


def make_graph(filepath, output_filepath, order, scale):
    filetype = filepath[-3:]
    if not filetype in ['png', 'svg']:
        print('File format not recognised!')
        print('Rename file (.svg, .png), or convert to the correct format and try again.')
        return

    print('(1/6) Finding path from {}'.format(filepath), flush=True)
    if filetype == 'svg':
        x, y = x_y_from_svg(filepath)
    elif filetype == 'png':
        x, y = x_y_from_png(filepath)

    N = order
    M = int(len(x) * scale) # == len(y)

    x_spline = spline_maker(x)
    y_spline = spline_maker(y)

    x = sampler(x_spline, M) 
    y = sampler(y_spline, M)

    x = np.array(x)
    y = np.array(y)
    
    # Subtract the average: removes 0th cos coeff, and centers graph around origo
    x = x - sum(x)/M
    y = y - sum(y)/M

    print('(2/6) Computing the Fourier transform matrix (this could take some time)', flush=True)
    if N > M:
        too_large_order_error_message(N, M)
        N = M
    else:
        print('\t(N = {}, M = {})'.format(N, M))
    fourier = Fourier_matrix(N, M)
    
    print('(3/6) Finding Fourier coefficients for x(t) and y(t)', flush=True)
    a, b = fourier.make_coeffs(x)
    c, d = fourier.make_coeffs(y)

    print('(4/6) Computing Fourier approximation for x(t) and y(t)', flush=True)
    x_appr = list(fourier.make_approximation(a, b, N))
    y_appr = list(fourier.make_approximation(c, d, N))

    # Close the curve:
    x_appr.append(x_appr[0])
    y_appr.append(y_appr[0])

    print('(5/6) Making plot and saving image', flush=True)
    plt.figure(figsize=(20,15))
    plt.axis('equal')
    plt.plot(list(x_appr), list(y_appr))
    plt.savefig(output_filepath)
    plt.close()
    
    print('(6/6) Writing LaTeX-code to file', flush=True)
    latex_simplest = latex_simplified_formula(a,b,c,d)
    latex_simple = latex_old_simplified_formula(a,b,c,d,6)
    latex_complete = latex_complete_formula(a,b,c,d,2, 10)

    with open('latex_simplest.tex', 'w') as f:
        f.write(latex_simplest)

    with open('latex_simple.tex', 'w') as f:
        f.write(latex_simple)

    with open('latex_complete.tex', 'w') as f:
        f.write(latex_complete)

    print('\nAll done!', flush=True)
