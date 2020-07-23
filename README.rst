==========
zodbverify
==========

Overview
========

Verify a ZODB by iterating and loading all records.
Problems are reported in detail.
A debugger is provided, together with decompilation information.

zodbverify is available as a standalone script and as addon for `plone.recipe.zope2instance`.


Usage
=====

Script
------

The verification runs on a plain ZODB file.
The Zope application is not started.

Run i.e.::

    bin/zodbverify -f var/filestorage/Data.fs

Usage::

    zodbverify [-h] -f ZODBFILE [-D] [-o OID]

    Verifies that all records in the database can be loaded.

    optional arguments:
      -h, --help            show this help message and exit
      -f ZODBFILE, --zodbfile ZODBFILE
                            Path to file-storage
      -D, --debug           pause to debug broken pickles
      -o OID, --oid OID     oid to inspect


plone.recipe.zope2instance integration
--------------------------------------

The verification runs in the context of the initialized Zope application.

Usage::

    ./bin/instance zodbverify [-h] [-D] [-o OID]

    Verifies that all records in the database can be loaded.

    optional arguments:
      -h, --help         show this help message and exit
      -D, --debug        pause to debug broken pickles
      -o OID, --oid OID  oid to inspect


Inspecting a single oid
-----------------------

The output of zodbverify gives you a list of all problems and the oid that are affected.

To inspect a single oid in detail you can pass one of these to zodbverify::

  ./bin/instance zodbverify -o 0x2e929f

This will output the pickle and the error for that oid.

By also adding the debug-switch you will get two pdb's while the script runs::

  ./bin/instance zodbverify -o 0x2e929f -D

  2020-03-11 10:40:24,972 INFO    [Zope:45][MainThread] Ready to handle requests
  The object is 'obj'
  The Zope instance is 'app'
  [4] > /Users/pbauer/workspace/dipf-intranet/src-mrd/zodbverify/src/zodbverify/verify_oid.py(52)verify_oid()
  -> pickle, state = storage.load(oid)

In the first pdb you have the object for the oid as `obj` and the zope instance as `app`. Before the second pdb the pickle will be disassembled the same way as when using zodbverify to pause to debug broken pickles without passing a oid.


Source Code
===========

Contributors please read the document `Process for Plone core's development <https://docs.plone.org/develop/coredev/docs/index.html>`_

Sources are at the `Plone code repository hosted at Github <https://github.com/plone/zodbverify>`_.
