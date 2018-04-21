#!/usr/bin/env python
from __future__ import unicode_literals

import unittest

import six

from pyangbind.lib.xpathhelper import YANGPathHelper
from tests.base import PyangBindTestCase


class MiscTests(PyangBindTestCase):
  yang_files = ['misc.yang']
  split_class_dir = True
  pyang_flags = ['--use-extmethods', '--use-xpathhelper']

  def setUp(self):
    self.path_helper = YANGPathHelper()
    self.instance = self.bindings.misc(path_helper=self.path_helper)

  # Check that we can ingest an OpenConfig style list entry
  # with a leafref to the key
  def test_001_setleafref(self):
    import bindings.a as misca
    a = misca.a()
    a.foo = "stringval"

    self.instance.a.append(a)
    self.assertEqual(six.text_type(self.instance.a["stringval"].foo), "stringval")
    self.assertEqual(self.instance.a["stringval"].config.foo, "stringval")

  def test_002_checklistkeytype(self):
    import bindings.b as miscb
    b = miscb.b()
    b.foo = "stringvalone"
    b.bar = "stringvaltwo"

    self.instance.b.append(b)
    self.assertIsInstance(self.instance.b.keys()[0], six.text_type)

  def test_003_checklistkeytype(self):
    import bindings.c as miscc
    c = miscc.c()
    c.one = 42

    self.instance.c.append(c)
    self.assertIsInstance(self.instance.c.keys()[0], int)


if __name__ == '__main__':
  unittest.main(exit=False)
