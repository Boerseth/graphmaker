import sys

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

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
    with Image.open(filename).rotate(270) as im:
        im_array = np.array(im)
    N,M = len(im_array[:,0]), len(im_array[0,:])
    im_list = [[pixel_to_binary(im_array[n,m,0]) for m in range(M)]
                                                    for n in range(N)]
    height = lambda v: im_list[v[0]][v[1]]
    size = min(N, M)
    return find_edge(height, size)


def x_y_from_png(filename):
    edge = get_edge_from_image(filename)
    x = [e[0] for e in edge]
    y = [e[1] for e in edge]
    return x, y
