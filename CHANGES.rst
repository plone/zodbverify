Changelog
=========

.. You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst

.. towncrier release notes start

1.2.0 (2022-07-06)
------------------

New features:


- Improve debugging output: show all objects that reference a oid.
  See `Philip's blog post <https://www.starzel.de/blog/zodb-debugging>`_ for more information.
  See also discussion in `pull request 8 <https://github.com/plone/zodbverify/pull/8>`_.
  [pbauer] (#8)


1.1.0 (2020-04-22)
------------------

New features:


- Show the affected oids for each error.
  Inspect a single oid.
  The idea is to run zodbverify on the whole database and from the output copy one oid and run it again to further inspect that object.
  [pbauer] (#6)


Bug fixes:


- Minor packaging updates. (#1)


1.0.2 (2019-08-08)
------------------

Bug fixes:


- Open Data.fs in read only mode. (#2)


1.0.1 (2019-05-09)
------------------

Bug fixes:


- Fix project description. [jensens] (#1)


1.0 (2019-05-09)
----------------

New features:


- Initial effort.
  Base code taken from `Products.CMFPlone` (created by @davisagli).
  Enhanced and packaged for more general Zope use.
  [dwt,jensens] (#1)


