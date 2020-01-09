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

    zodbverify [-h] -f ZODBFILE [-D]

    Verifies that all records in the database can be loaded.

    optional arguments:
      -h, --help            show this help message and exit
      -f ZODBFILE, --zodbfile ZODBFILE
      -D, --debug           pause to debug broken pickles


plone.recipe.zope2instance integration
--------------------------------------

The verification runs in the context of the initialized Zope application.

Usage::

    ./bin/instance zodbverify [-h] [-D]

    Verifies that all records in the database can be loaded.

    optional arguments:
      -h, --help   show this help message and exit
      -D, --debug  pause to debug broken pickles


Source Code
===========

Contributors please read the document `Process for Plone core's development <https://docs.plone.org/develop/coredev/docs/index.html>`_

Sources are at the `Plone code repository hosted at Github <https://github.com/plone/zodbverify>`_.
