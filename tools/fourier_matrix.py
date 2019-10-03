import numpy as np

class Fourier_matrix:
    def __init__(self, N, M):
        self.N = N
        self.M = M
        self.COS = np.fromfunction(lambda n, m: np.cos((n+1) * m * 2 * np.pi / M), (N,M), dtype=float)
        self.SIN = np.fromfunction(lambda n, m: np.sin((n+1) * m * 2 * np.pi / M), (N,M), dtype=float)
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
