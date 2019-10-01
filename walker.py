import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import pytest

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


def plot_edge_from_image(filename):
    edge = get_edge_from_image(filename)
    x, y = cartesian_from_tuple_list(edge)
    plt.plot(x, y)
    plt.show()
    
    
def normalised(numbers):
    avg = sum(numbers)/len(numbers)
    return [number - avg for number in numbers]


def spline_maker(vals):
    N = len(vals)
    def spline(x):
        i = int(x * N)
        t = (x * N) % 1
        return vals[i-1] * (1 - t) + vals[i] * t
    return spline
    

def spline_edge_from_image(filename):
    edge_vectors = [np.array(point) for point in get_edge_from_image(filename)]
    avg = sum(edge_vectors) / len(edge_vectors)
    edge_vectors = [v - avg for v in edge_vectors]
    N = len(edge_vectors)
    spline = spline_maker(edge_vectors[1:])
    t = np.linspace(0, 1, 16000)[:-1]
    return [spline(t_) for t_ in t]

def plot_splined(filename):
    edge_points = spline_edge_from_image(filename)
    x, y = cartesian_from_tuple_list(edge_points)
    plt.plot(x, y)
    plt.show()


def make_trigs(t, N):
    return ([np.cos(n * np.pi * t) for n in range(N)],
            [np.sin(n * np.pi * t) for n in range(N)])

def fourier_coeffs(f, N):
    t = np.linspace(0, 1, len(f) + 1)[:-1]
    COS, SIN = make_trigs(t, N) 
    cos_coeffs = [f.dot(COS_) for COS_ in COS]
    sin_coeffs = [f.dot(SIN_) for SIN_ in SIN]
    return (cos_coeffs, sin_coeffs)


def fourier_series(coeffs):
    def f(x):
        return sum(c[0] * np.cos(n * np.pi * x) 
                 + c[1] * np.sin(n * np.pi * x) 
                   for n, c in enumerate(zip(coeffs)))
    return f



#==============================================================================
# T E S T S
#==============================================================================

def test_no_starting_point_raises_exception():
    my_array = [[0,0],
                [0,0]]
    height = lambda v: my_array[v[0]][v[1]]
    size = 2
    with pytest.raises(CannotFindOutlineException):
        find_starting_point(height, size)


def test_starting_point_pointed_left():
    my_array = [[0,0],
                [0,1]]
    height = lambda v: my_array[v[0]][v[1]]
    size = 2
    left, right = find_starting_point(height, size)
    assert np.allclose(left, np.array([0,1]))
    assert np.allclose(right, np.array([1,1]))


def test_starting_point_pointed_up():
    my_array = [[0,1],
                [0,1]]
    height = lambda v: my_array[v[0]][v[1]]
    size = 2
    left, right = find_starting_point(height, size)
    assert np.allclose(left, np.array([0,0]))
    assert np.allclose(right, np.array([0,1]))


def test_starting_point_larger_pointed_left():
    my_array = [[0,0,0,0],
                [0,0,0,0],
                [0,0,0,1],
                [0,0,0,1]]
    height = lambda v: my_array[v[0]][v[1]]
    size = 4
    left, right = find_starting_point(height, size)
    assert np.allclose(left, np.array([2,2]))
    assert np.allclose(right, np.array([2,3]))


def test_starting_point_larger_pointed_up():
    my_array = [[0,0,0,0],
                [0,0,0,0],
                [0,0,0,0],
                [0,0,0,1]]
    height = lambda v: my_array[v[0]][v[1]]
    size = 4
    left, right = find_starting_point(height, size)
    assert np.allclose(left, np.array([2,3]))
    assert np.allclose(right, np.array([3,3]))


def test_simple():
    my_array = [[0,0,0],
                [0,1,0],
                [0,0,0]]
    height = lambda v: my_array[v[0]][v[1]]
    size = 3
    edge = find_edge(height, size)
    assert len(edge) == 5
    


def test_square():
    my_array = [[0,0,0,0],
                [0,1,1,0],
                [0,1,1,0],
                [0,0,0,0],]
    starting_point = [np.array([2,0]),np.array([2,1])]
    height = lambda v: my_array[v[0]][v[1]]
    my_walker = Walker(height, starting_point[0], starting_point[1])
    my_walker.make_step() # should now be at [1,0], [1,1]
    left_foot, right_foot = my_walker.get_feet_positions()
    assert left_foot[0] == right_foot[0]
    assert left_foot[1] == 0
    assert right_foot[1] == 1
    left_path = []
    right_path = []
    while not my_walker.has_returned:
        my_walker.make_step()
        left, right = my_walker.get_feet_positions()
        left_path.append(left)
        right_path.append(right)
    end_left, end_right = my_walker.get_feet_positions()
    assert np.allclose(end_left, starting_point[0])
    assert np.allclose(end_right, starting_point[1])
    left_x = [l[0] for l in left_path]
    left_y = [l[1] for l in left_path]
    right_x = [r[0] for r in right_path]
    right_y = [r[1] for r in right_path]
    plt.plot(left_x, left_y)
    plt.plot(right_x, right_y)
    plt.show()


def test_arbitrary():
    my_array = [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,1,1,0,0,0,0,1,0,0,1,0,0,0,0],
                [0,1,1,1,1,0,1,1,0,0,1,1,0,0,0],
                [0,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
                [0,1,1,1,1,1,1,1,1,1,0,0,1,0,0],
                [0,0,1,1,1,0,1,1,1,1,0,0,1,1,0],
                [0,0,1,1,1,0,1,0,1,1,1,0,1,1,0],
                [0,0,1,0,0,0,0,0,1,1,1,0,1,1,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],]
    starting_point = [np.array([2,0]),np.array([2,1])]
    height = lambda v: my_array[v[0]][v[1]]
    my_walker = Walker(height, starting_point[0], starting_point[1])
    left_foot, right_foot = my_walker.get_feet_positions()
    left_path = [left_foot]
    right_path = [right_foot]
    while not my_walker.has_returned:
        my_walker.make_step()
        left, right = my_walker.get_feet_positions()
        left_path.append(left)
        right_path.append(right)
    end_left, end_right = my_walker.get_feet_positions()
    assert np.allclose(end_left, starting_point[0])
    assert np.allclose(end_right, starting_point[1])
    left_x = [l[0] for l in left_path]
    left_y = [l[1] for l in left_path]
    right_x = [r[0] for r in right_path]
    right_y = [r[1] for r in right_path]
    avg_x = [(l+r)/2 for l, r in zip(left_x, right_x)]
    avg_y = [(l+r)/2 for l, r in zip(left_y, right_y)]
    plt.plot(left_x, left_y)
    plt.plot(right_x, right_y)
    plt.plot(avg_x, avg_y)
    plt.show()


def all_tests():
    test_square()
    test_arbitrary()
    test_no_starting_point_raises_exception()
    test_starting_point_pointed_left()
    test_starting_point_pointed_up()
    test_starting_point_larger_pointed_left()
    test_starting_point_larger_pointed_up()
    test_simple()
    print("All tests ran successfully")


if __name__ == "__main__":
    all_tests()
    filename = "image.png"
    plot_edge_from_image(filename)
    plot_splined(filename)
     


















