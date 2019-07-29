import argparse
from lft.app import App


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("number", type=int, help="The number of nodes")
    args = parser.parse_args()
    app = App(args.number)
    app.start()


if __name__ == "__main__":
    main()
