# -*- coding: utf-8 -*-
from persistent import Persistent
from ZODB.Connection import TransactionMetaData
from zodbverify.verify import class_is_persistent
from zodbverify.verify import verify_record
from zodbverify.verify import verify_zodb

import io
import logging
import os
import pickle
import shutil
import tempfile
import transaction
import unittest
import ZODB
import ZODB.FileStorage


OID = b"\x00\x00\x00\x00\x00\x00\x00\x2a"


class APersistentThing(Persistent):
    pass


class ANonPersistentThing(object):
    pass


def make_record(class_info, state=None):
    """Build a ZODB record: the class metadata pickle plus the state pickle."""
    output = io.BytesIO()
    pickler = pickle.Pickler(output, protocol=3)
    pickler.dump(class_info)
    pickler.dump({} if state is None else state)
    return output.getvalue()


class TestClassIsPersistent(unittest.TestCase):
    def test_direct_class_reference(self):
        self.assertEqual(
            class_is_persistent(APersistentThing),
            (True, "zodbverify.tests.APersistentThing"),
        )
        self.assertEqual(
            class_is_persistent(ANonPersistentThing),
            (False, "zodbverify.tests.ANonPersistentThing"),
        )

    def test_class_and_args_tuple(self):
        self.assertEqual(
            class_is_persistent((APersistentThing, ())),
            (True, "zodbverify.tests.APersistentThing"),
        )
        self.assertEqual(
            class_is_persistent((ANonPersistentThing, None)),
            (False, "zodbverify.tests.ANonPersistentThing"),
        )

    def test_old_style_module_and_name_tuple(self):
        self.assertEqual(
            class_is_persistent((("zodbverify.tests", "APersistentThing"), ())),
            (True, "zodbverify.tests.APersistentThing"),
        )
        self.assertEqual(
            class_is_persistent((("zodbverify.tests", "ANonPersistentThing"), ())),
            (False, "zodbverify.tests.ANonPersistentThing"),
        )

    def test_broken_class_is_not_reported(self):
        # ZODB replaces a class whose module is gone with a PersistentBroken
        # subclass while loading, so it must not be reported here. Missing
        # modules are reported by the unpickling step instead.
        is_persistent, class_name = class_is_persistent(
            (("no.such.module", "Gone"), ())
        )
        self.assertTrue(is_persistent)
        self.assertEqual(class_name, "no.such.module.Gone")


class TestVerifyRecord(unittest.TestCase):
    def test_persistent_class_passes(self):
        self.assertEqual(
            verify_record(OID, make_record(APersistentThing)), (True, None)
        )

    def test_non_persistent_class_is_reported(self):
        success, msg = verify_record(OID, make_record(ANonPersistentThing))
        self.assertFalse(success)
        self.assertEqual(msg, "NotPersistent: zodbverify.tests.ANonPersistentThing")

    def test_unloadable_record_still_reports_its_exception(self):
        success, msg = verify_record(OID, b"this is not a pickle")
        self.assertFalse(success)
        self.assertNotIn("NotPersistent", msg)


class TestVerifyZODB(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "Data.fs")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _store(self, oid, record):
        storage = ZODB.FileStorage.FileStorage(self.path)
        try:
            txn = TransactionMetaData()
            storage.tpc_begin(txn)
            storage.store(oid, storage.load(oid)[1], record, b"", txn)
            storage.tpc_vote(txn)
            storage.tpc_finish(txn)
        finally:
            storage.close()

    def _make_db_with_one_object(self):
        storage = ZODB.FileStorage.FileStorage(self.path)
        db = ZODB.DB(storage)
        connection = db.open()
        connection.root()["thing"] = APersistentThing()
        transaction.commit()
        oid = connection.root()["thing"]._p_oid
        db.close()
        return oid

    def _verify(self):
        storage = ZODB.FileStorage.FileStorage(self.path, read_only=True)
        try:
            with self.assertLogs("zodbverify", level=logging.INFO) as logs:
                verify_zodb(storage)
        finally:
            storage.close()
        return "\n".join(logs.output)

    def test_clean_database_has_no_findings(self):
        self._make_db_with_one_object()
        output = self._verify()
        self.assertIn("Found 0 records that could not be loaded.", output)

    def test_record_with_non_persistent_class_is_found(self):
        oid = self._make_db_with_one_object()
        self._store(oid, make_record(ANonPersistentThing))
        output = self._verify()
        self.assertIn("Found 1 records that could not be loaded.", output)
        self.assertIn("NotPersistent: zodbverify.tests.ANonPersistentThing", output)
