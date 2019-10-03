import sys
import time
import numpy as np
import matplotlib.pyplot as plt

from tools.fourier_matrix import Fourier_matrix
from tools.path_finder_svg import x_y_from_svg
from tools.path_finder_png import x_y_from_png
from tools.tex_maker import latex_complete_formula, latex_simplified_formula



def make_graph(filepath, output_filepath, order):
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
    M = len(x) # == len(y)

    x = np.array(x)
    y = np.array(y)
    x = x - sum(x)/M
    y = y - sum(y)/M

    x_scope = (min(x)-20, max(x)+20)
    y_scope = (min(y)-20, max(y)+20)
    scope = (min(min(x), min(y)) - 20,
             max(max(x), max(y)) + 20)

    print('(2/6) Computing the Fourier transform matrix (this could take some time)', flush=True)
    fourier = Fourier_matrix(N, M)
    print('(3/6) Finding Fourier coefficients for x(t) and y(t)', flush=True)
    a, b = fourier.make_coeffs(x)
    c, d = fourier.make_coeffs(y)


    print('(4/6) Computing Fourier approximation for x(t) and y(t)', flush=True)
    x_appr = fourier.make_approximation(a, b, N)
    y_appr = fourier.make_approximation(c, d, N)

    print('(5/6) Make plot and save image', flush=True)
    plt.figure(figsize=(20,15))
    plt.axis('equal')
    plt.plot(list(x_appr), list(y_appr))
    plt.savefig(output_filepath)
    plt.close()
    
    print('(6/6) Write LaTeX-code to file', flush=True)
    latex_simplified = latex_simplified_formula(a,b,c,d,4)
    latex_complete = latex_complete_formula(a,b,c,d,2, 10)

    with open('latex_simple.tex', 'w') as f:
        f.write(latex_simplified)

    with open('latex_complete.tex', 'w') as f:
        f.write(latex_complete)

    print('\nAll done!', flush=True)
