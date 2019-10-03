import sys

from tools.make_graph import make_graph



if __name__ == "__main__":
    filepath = sys.argv[1]
    order = int(sys.argv[2])
    make_graph(filepath, order)
