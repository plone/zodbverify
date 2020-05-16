# -*- coding: utf-8 -*-
from collections import defaultdict
from ZODB.interfaces import IStorageCurrentRecordIteration
from ZODB.serialize import get_refs
from ZODB.utils import get_pickle_metadata
from ZODB.utils import oid_repr
from ZODB.utils import p64
from zodbverify.verify import verify_record

import logging
import pdb
import traceback
import ZODB


logger = logging.getLogger("zodbverify")


class Refbuilder(object):

    def __init__(self, storage):
        self.storage = storage
        self.seen = []
        self.refs = defaultdict(list)
        self.stop_recurse = [
            p64(0x00),  # persistent.mapping.PersistentMapping
            p64(0x01),  # OFS.Application.Application
            p64(0x11),  # Products.CMFPlone.Portal.PloneSite
        ]

    def build_ref_tree(self):
        logger.info('Building a reference-tree of ZODB...')
        count = 0
        next_ = None
        while True:
            count += 1
            oid, tid, data, next_ = self.storage.record_iternext(next_)

            # For each oid create a list of oids that reference it
            # Can be used for reverse lookup similar to what fsoids.py
            # in ZODB does.
            # We store integers since that uses less memory.
            oid_refs = get_refs(data)
            if oid_refs:
                for referenced_oid, class_info in oid_refs:
                    self.refs[referenced_oid].append(oid)
            if next_ is None:
                break
            if not count % 5000:
                logger.info('Objects: {}'.format(count))
        logger.info('Created a reference-dict for {} objects.\n'.format(count))

    def get_refs(self, oid, level=0, max_level=10):
        for ref in self.refs[oid]:
            if ref in self.seen:
                continue
            level += 1
            if level > max_level:
                logger.info(' 8< --------------- >8 Stop after level {}!\n'.format(max_level))
                continue
            self.seen.append(ref)
            pick, state = self.storage.load(ref)
            class_info = '%s.%s' % get_pickle_metadata(pick)
            logger.info('{} {} at level {}'.format(oid_repr(ref), class_info, level))
            if oid in self.stop_recurse:
                logger.info(' 8< --------------- >8 Stop at root objects\n')
                continue
            self.get_refs(ref, level)


def verify_oid(storage, oid, debug=False, app=None):
    if not IStorageCurrentRecordIteration.providedBy(storage):
        raise TypeError(
            "ZODB storage {} does not implement record_iternext".format(storage)
        )

    try:
        # by default expect a 8-byte string (e.g. '0x22d17d')
        # transform to a 64-bit long integer (e.g. b'\x00\x00\x00\x00\x00"\xd1}')
        as_int = int(oid, 0)
        oid = p64(as_int)
    except ValueError:
        # probably already a 64-bit long integer
        pass

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

    refbuilder = Refbuilder(storage)
    refbuilder.build_ref_tree()
    logger.info('\nThis oid is referenced by:\n')
    refbuilder.get_refs(oid)
