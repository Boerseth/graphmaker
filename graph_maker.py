import sys

from tools.make_graph import make_graph



if __name__ == "__main__":
    filepath = sys.argv[1]
    output_filepath = sys.argv[2]
    order = int(sys.argv[3])

    if len(sys.argv) == 5:
        scale = eval(sys.argv[4])
    else:
        scale = 1

    make_graph(filepath, output_filepath, order, scale)
