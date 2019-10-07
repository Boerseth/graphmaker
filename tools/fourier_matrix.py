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
        assert len(f) == self.M
        a = self.COS.dot(f) / self.M # Integral, divide by M to normalise
        b = self.SIN.dot(f) / self.M
        return a, b


    def make_approximation(self, a, b, n):
        assert n <= self.N

        if n == self.N:
            sieve = np.array([1.0]*self.N)
        elif n < 0:
            sieve = np.array([0.0]*self.N)
        else:
            n = int(n)
            t = n % 1
            sieve = np.array([1.0]*n + [t] + [0.0]*(self.N - n - 1))

        a_sieved = a * sieve
        b_sieved = b * sieve
        f_appr = self.COST.dot(a_sieved) + self.SINT.dot(b_sieved)

        return f_appr
