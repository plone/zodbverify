# -*- coding: utf-8 -*-
from zodbverify.verify import verify_zodb
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


def zopectl_entry(self, arg):
    options = parser.parse_args(arg.split(" ") if arg else [])

    logging.basicConfig(level=logging.INFO)
    make_wsgi_app({}, self.options.configfile)
    app = Zope2.app()
    verify_zodb(app._p_jar._db._storage, debug=options.debug)
