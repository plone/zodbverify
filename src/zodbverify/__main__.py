import argparse
import logging
import sys

from ZODB.FileStorage import FileStorage

from .verify import verify_zodb


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(
        prog="zodbverify",
        description="Verifies that all records in the database can be loaded.",
    )
    parser.add_argument(
        "-f",
        "--zodbfile",
        action="store",
        dest="zodbfile",
        required=True,
        help="Path to file-storage",
    )
    parser.add_argument(
        "-D",
        "--debug",
        action="store_true",
        dest="debug",
        help="pause to debug broken pickles",
    )
    options = parser.parse_args(argv[1:])

    logging.basicConfig(level=logging.INFO)
    storage = FileStorage(options.zodbfile)
    verify_zodb(storage, debug=options.debug)


if __name__ == "__main__":
    main()
