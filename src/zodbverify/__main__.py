import argparse
import logging
import sys

from ZODB.FileStorage import FileStorage

from .verify import verify_zodb
from .verify_oid import verify_oid


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
    parser.add_argument(
        "-o",
        "--oid",
        action="store",
        dest="oid",
        help="oid to inspect",
    )
    options = parser.parse_args(argv[1:])

    logging.basicConfig(level=logging.INFO)
    storage = FileStorage(options.zodbfile, read_only=True)
    if options.oid:
        verify_oid(storage, options.oid, debug=options.debug)
    else:
        verify_zodb(storage, debug=options.debug)


if __name__ == "__main__":
    main()
