# -*- coding: utf-8 -*-
from ZODB.interfaces import IStorageCurrentRecordIteration
from ZODB.utils import oid_repr
from ZODB.utils import p64
from zodbverify.verify import verify_record

import logging
import pdb
import traceback
import ZODB


logger = logging.getLogger("zodbverify")


def verify_oid(storage, oid, debug=False, app=None):
    if not IStorageCurrentRecordIteration.providedBy(storage):
        raise TypeError(
            "ZODB storage {} does not implement record_iternext".format(storage)
        )

    if not isinstance(oid, bytes):
        oid = p64(int(oid, 0))

    if app:
        # use exitsing zope instance.
        # only available when used as ./bin/instance zodbverify -o XXX
        connection = app._p_jar
    else:
        # connect to database to be able to load the object
        db = ZODB.DB(storage)
        connection = db.open()

    try:
        obj = connection.get(oid)
        try:
            logger.info("\nObject as dict:\n{}".format(vars(obj)))
        except TypeError:
            pass
        if debug:
            hint = "\nThe object is 'obj'"
            if app:
                hint += "\nThe Zope instance is 'app'"
            logger.info(hint)
            pdb.set_trace()
    except Exception as e:
        logger.info("Could not load object")
        logger.info(traceback.format_exc())
        if debug:
            pdb.set_trace()

    pickle, state = storage.load(oid)

    success, msg = verify_record(oid, pickle, debug)
    if not success:
        logger.info('{}: {}'.format(msg, oid_repr(oid)))
