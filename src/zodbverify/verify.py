# -*- coding: utf-8 -*-
from collections import defaultdict
from persistent import Persistent
from ZODB.broken import Broken
from ZODB.broken import find_global
from ZODB.interfaces import IStorageCurrentRecordIteration
from ZODB.serialize import PersistentUnpickler
from ZODB.utils import oid_repr

import io
import logging
import pdb
import pickletools
import traceback


logger = logging.getLogger("zodbverify")


def verify_zodb(storage, debug=False):
    if not IStorageCurrentRecordIteration.providedBy(storage):
        raise TypeError(
            "ZODB storage {} does not implement record_iternext".format(storage)
        )

    logger.info("Scanning ZODB...")

    next_ = None
    count = 0
    errors = 0
    issues = defaultdict(list)
    oids = []
    while True:
        count += 1
        oid, tid, data, next_ = storage.record_iternext(next_)
        logger.debug("Verifying {}".format(oid))
        success, msg = verify_record(oid, data, debug)
        if not success:
            errors += 1
            issues[msg].append(oid_repr(oid))
            # issues.append(msg)
            oids.append(oid)
        if next_ is None:
            break

    msg = ""
    order = sorted(issues, key=lambda k: len(issues[k]), reverse=True)
    for key in order:
        oids = issues[key]
        msg += "{}: {}\n{}\n\n".format(key, len(oids), ' '.join(oids))
    logger.info(
        "Done! Scanned {} records. \n"
        "Found {} records that could not be loaded. \n"
        "Exceptions, how often they happened and which oids are affected: \n\n"
        "{}".format(count, errors, msg)
    )


def verify_record(oid, data, debug=False):
    input_file = io.BytesIO(data)
    unpickler = PersistentUnpickler(None, persistent_load, input_file)
    class_info = "unknown"
    pos = None
    try:
        class_info = unpickler.load()
        pos = input_file.tell()
        unpickler.load()
    except Exception as e:
        input_file.seek(0)
        pickle = input_file.read()
        logger.info("\nCould not process {} record {} ({!r}):".format(class_info, oid_repr(oid), oid))
        logger.info(repr(pickle))
        logger.info(traceback.format_exc())
        if debug and pos is not None:
            try:
                pickletools.dis(pickle[pos:])
            except Exception:
                # ignore exceptions while disassembling the pickle since the
                # real issue is that it references a unavailable module
                pass
            finally:
                pdb.set_trace()
        elif debug and pos is None:
            pdb.set_trace()
        # The same issues should have the same msg
        msg = "{}: {}".format(e.__class__.__name__, str(e))
        return False, msg

    is_persistent, class_name = class_is_persistent(class_info)
    if not is_persistent:
        logger.info(
            "\nRecord {} ({!r}) has class {}, "
            "which is not a subclass of persistent.Persistent.".format(
                oid_repr(oid), oid, class_name
            )
        )
        if debug:
            pdb.set_trace()
        return False, "NotPersistent: {}".format(class_name)
    return True, None


def class_is_persistent(class_info):
    """Check the class of a record against persistent.Persistent.

    Every record in a ZODB is an instance of a Persistent subclass. It is
    possible to end up with a record that is not, for instance by using
    zodbupdate to rename a persistent class to a non-persistent one. Such a
    record unpickles fine on its own, so the checks above do not notice it,
    but loading it through a connection fails later with
    ``TypeError: Cache values must be persistent objects``.

    The class is resolved the same way ZODB.serialize.ObjectReader.getGhost
    resolves it. Returns a ``(is_persistent, class_name)`` tuple.
    """
    klass = class_info
    if isinstance(klass, tuple):
        klass, args = klass
        if isinstance(klass, tuple):
            # old style (module_name, class_name) reference
            klass = find_global(*klass)

    if not isinstance(klass, type):
        return False, repr(klass)

    class_name = "{}.{}".format(klass.__module__, klass.__name__)
    if issubclass(klass, Broken):
        # ZODB turns these into a PersistentBroken subclass while loading,
        # so they are not what this check is looking for. A class that is
        # broken because its module is gone is reported by the unpickling
        # above instead.
        return True, class_name
    return issubclass(klass, Persistent), class_name


def persistent_load(ref):
    pass
