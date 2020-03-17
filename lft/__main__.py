import argparse
from pathlib import Path


def main():
    try:
        from lft.app import InstantApp, RecordApp, ReplayApp
        from lft.app.app import Mode
    except ImportError:
        print('Requirements are not satisfied. Please use following command to install the requirements.')
        print('> pip install -U "lft[app]"')
        exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("mode", type=Mode, default=Mode.instant.value, nargs='?',
                        help="App running mode, [instant|record|replay], (default: %(default)s)")
    parser.add_argument("--number", "-n", type=int, default=4, required=False,
                        help="Number of nodes(ignored on replay mode), (default: %(default)s)")
    parser.add_argument("--data", "-d", type=Path, default=Path("data"), required=False,
                        help="Record data path(ignored on instant mode), (default: %(default)s)")
    parser.add_argument("--target", "-t", type=bytes.fromhex, default=b"", required=False,
                        help="Target node ID for replay(only for replay mode)")

    args = parser.parse_args()
    if args.mode == Mode.instant:
        app = InstantApp(args.number)
    elif args.mode == Mode.record:
        app = RecordApp(args.number, args.data)
    elif args.mode == Mode.replay:
        app = ReplayApp(args.data, args.target)
    else:
        raise RuntimeError("Invalid mode, {args.mode}")
    app.start()
    app.close()


if __name__ == "__main__":
    main()
