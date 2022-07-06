# -*- coding: utf-8 -*-
from collections import defaultdict
from ZODB.interfaces import IStorageCurrentRecordIteration
from ZODB.serialize import get_refs
from ZODB.utils import get_pickle_metadata
from ZODB.utils import oid_repr
from ZODB.utils import repr_to_oid
from ZODB.utils import p64
from ZODB.utils import tid_repr
from zodbverify.verify import verify_record

import json
import logging
import os
import pdb
import traceback
import ZODB


logger = logging.getLogger("zodbverify")


class Refbuilder(object):

    def __init__(self, storage, connection):
        self.storage = storage
        self.connection = connection
        self.seen = []
        self.refs = defaultdict(list)
        self.msg = []
        self.stop_recurse = [
            '0x00',  # persistent.mapping.PersistentMapping
            '0x01',  # OFS.Application.Application
            '0x11',  # Products.CMFPlone.Portal.PloneSite
        ]

    def get_oid_report(self, oid, level=0, max_level=600, verbose=False):
        self.msg.append('The oid {} is referenced by:\n'.format(oid))
        self.inspect_reference_tree(oid, level=0, max_level=600, verbose=verbose)
        logger.info('\n'.join(self.msg))

    def _build_ref_tree(self):
        logger.info('Building a reference-tree of ZODB...')
        count = 0
        next_ = None
        while True:
            count += 1
            oid, tid, data, next_ = self.storage.record_iternext(next_)

            # For each oid create a list of oids that reference it
            # Can be used for reverse lookup similar to what fsoids.py
            # in ZODB does.
            oid_refs = get_refs(data)
            if oid_refs:
                for referenced_oid, class_info in oid_refs:
                    self.refs[oid_repr(referenced_oid)].append(oid_repr(oid))
            if next_ is None:
                break
            if not count % 10000:
                logger.info('Objects: {}'.format(count))
        logger.info('Created a reference-dict for {} objects.\n'.format(count))

    def inspect_reference_tree(self, oid, level=0, max_level=600, verbose=False):
        if oid not in self.refs:
            logger.debug('The oid {} does not exist!'.format(oid))
            return
        child_pickle, state = self.storage.load(repr_to_oid(oid))
        child_class_info = '%s.%s' % get_pickle_metadata(child_pickle)

        for ref in self.refs[oid]:
            if ref in self.seen:
                continue
            level += 1
            if level > max_level:
                msg = '8< --------------- >8 Stop after level {}!\n'.format(max_level)
                self.msg.append(msg)
                logger.debug(msg)
                continue
            self.seen.append(ref)
            pick, state = self.storage.load(repr_to_oid(ref))
            class_info = '%s.%s' % get_pickle_metadata(pick)
            name = None
            if verbose:
                name = self.get_id_or_attr_name(oid=oid, parent_oid=ref)

            if name:
                msg = '{} ({}) is {} for {} ({}) at level {}'.format(oid, child_class_info, name, ref, class_info, level)
            else:
                msg = '{} ({}) is referenced by {} ({}) at level {}'.format(oid, child_class_info, ref, class_info, level)
            self.msg.append(msg)
            logger.debug(msg)

            if oid in self.stop_recurse:
                msg = '8< --------------- >8 Stop at root objects'
                self.msg.append(msg)
                logger.debug(msg)
                continue
            self.inspect_reference_tree(ref, level=level, verbose=verbose)

    @property
    def root_oid(self):
        return self.connection.root._root._p_oid

    def oid_or_repr_to_oid(self, oid_or_repr):
        if isinstance(oid_or_repr, bytes):
            return oid_or_repr
        return repr_to_oid(oid_or_repr)

    def oid_or_repr_to_repr(self, oid_or_repr):
        if isinstance(oid_or_repr, bytes):
            return oid_repr(oid_or_repr)
        return oid_or_repr

    # Do not use cache decorators, let ZODB do its caching.
    def get_obj(self, oid):
        u"""Get the object from its `oid'."""
        oid = self.oid_or_repr_to_oid(oid)
        obj = self.connection.get(oid)
        obj._p_activate()
        return obj

    # @instance.memoize
    def get_obj_as_str(self, oid):
        try:
            return str(self.get_obj(oid))
        except Exception:
            return '<error>'

    # @instance.memoize
    def get_physical_path(self, oid):
        try:
            return self.get_obj(oid).getPhysicalPath()
        except Exception:
            return None

    # @instance.memoize
    def get_id(self, oid):
        obj = self.get_obj(oid)
        if oid == self.root_oid:
            return 'Root'
        getId = getattr(obj, 'getId', None)
        if getId:
            try:
                return getId()
            except:  # noqa
                pass
        return getattr(obj, 'id', None)

    # @instance.memoize
    def get_attr_name(self, oid, parent_oid):
        oid = self.oid_or_repr_to_oid(oid)
        obj = self.get_obj(oid)
        parent = self.get_obj(parent_oid)
        names_and_values = ((name, getattr(parent, name, None)) for name in dir(parent))
        return next((name for (name, value) in names_and_values if value is obj), None)

    # @instance.memoize
    def get_id_or_attr_name(self, oid, parent_oid=None):
        identifier = self.get_id(oid)
        if identifier:
            return identifier

        return self.get_attr_name(oid, parent_oid) if parent_oid else None

    def load_reference_tree(self):
        path = self._get_reference_cache_path()
        if os.path.exists(path):
            with open(path, 'r') as f:
                logger.info('Loading json reference-cache from {}'.format(path))
                self.refs = json.load(f)
        else:
            self._build_ref_tree()
            self._store_reference_cache()

    def _store_reference_cache(self):
        path = self._get_reference_cache_path()
        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(path, 'w') as f:
            json.dump(self.refs, f)
        logger.info('Save reference-cache as {}'.format(path))

    def _get_reference_cache_path(self):
        cache_dir = os.path.join(os.path.expanduser('~'), '.cache', 'zodbverify')
        last_tid = tid_repr(self.storage.lastTransaction())
        return os.path.join(cache_dir, 'zodb_references_{}.json'.format(last_tid))


def verify_oid(storage, oid, debug=False, app=None):
    if not IStorageCurrentRecordIteration.providedBy(storage):
        raise TypeError(
            "ZODB storage {} does not implement record_iternext".format(storage)
        )

    try:
        # by default expect a 8-byte string (e.g. '0x22d17d')
        # transform to a 64-bit long integer (e.g. b'\x00\x00\x00\x00\x00"\xd1}')
        oid = repr_to_oid(oid)
    except:
        pass

    if app:
        # use existing zope instance.
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

    refbuilder = Refbuilder(storage, connection)
    refbuilder.load_reference_tree()
    refbuilder.get_oid_report(oid_repr(oid), verbose=True)
