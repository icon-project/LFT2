import argparse
from lft.app import App


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("node_num", type=int, help="Provide the number of nodes")
    args = parser.parse_args()
    app = App(args.node_num)
    app.start()


if __name__ == "__main__":
    main()
