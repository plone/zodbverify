# -*- coding: utf-8 -*-
from zodbverify.verify import verify_zodb
from zodbverify.verify_oid import verify_oid
from Zope2.Startup.run import make_wsgi_app

import argparse
import logging
import sys
import Zope2

parser = argparse.ArgumentParser(
    prog=sys.argv[0] + " zodbverify",
    description="Verifies that all records in the database can be loaded.",
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


def zopectl_entry(self, arg):
    options = parser.parse_args(arg.split(" ") if arg else [])

    logging.basicConfig(level=logging.INFO)
    make_wsgi_app({}, self.options.configfile)
    app = Zope2.app()
    storage = app._p_jar._db._storage
    if options.oid:
        verify_oid(storage, options.oid, debug=options.debug, app=app)
    else:
        verify_zodb(storage, debug=options.debug)
