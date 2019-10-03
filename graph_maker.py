import sys

from tools.make_graph import make_graph



if __name__ == "__main__":
    filepath = sys.argv[1]
    output_filepath = sys.argv[2]
    order = int(sys.argv[3])

    make_graph(filepath, output_filepath, order)
