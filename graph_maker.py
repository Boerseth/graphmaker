import sys

import numpy as np
import matplotlib.pyplot as plt
import imageio
from PIL import Image

from path_finder_png import *
from path_finder_svg import *
from tex_maker import *



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

    fourier = Fourier_matrix(N, M)
    a, b = fourier.make_coeffs(x)
    c, d = fourier.make_coeffs(y)

    x_appr = fourier.make_approximation(a, b, N)
    y_appr = fourier.make_approximation(c, d, N)

    # Make plot
    plt.figure(figsize=(20,15))
    plt.axis("equal")
    plt.plot(list(x_appr), list(y_appr))
    figurename = "{}.jpg".format(filepath[:-4])
    plt.savefig(figurename)
    
    latex_simplified = latex_simplified_formula(a,b,c,d,4)
    latex_complete = latex_complete_formula(a,b,c,d,2, 10)

    with open('lsimp.tex', 'w') as f:
        f.write(latex_simplified)

    with open('lcomp.tex', 'w') as f:
        f.write(latex_complete)
