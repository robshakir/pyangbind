#!/usr/bin/env python
from __future__ import unicode_literals

import json
import os.path
import unittest
from bitarray import bitarray
from decimal import Decimal

import pyangbind.lib.pybindJSON as pbJ
import pyangbind.lib.serialise as pbS
from pyangbind.lib.serialise import pybindJSONDecoder
from pyangbind.lib.xpathhelper import YANGPathHelper

from tests.base import PyangBindTestCase


class RoundtripTests(PyangBindTestCase):
    yang_files = ["roundtrip.yang", "remote.yang"]
    maxDiff = None

    def setUp(self):
        self.yang_helper = YANGPathHelper()
        self.rt_obj = self.bindings.roundtrip(path_helper=self.yang_helper)

    def test_ietf_roundtrip_simple(self):
        self.rt_obj.a.idref = "VALUE_TWO"
        j = pbJ.dumps(self.rt_obj, mode="ietf")
        pbS.pybindJSONDecoder.load_ietf_json(json.loads(j), None, None, obj=self.rt_obj)

    def test_roundtrip_simple(self):
        self.rt_obj.a.idref = "VALUE_TWO"
        j = pbJ.dumps(self.rt_obj)
        pbS.pybindJSONDecoder.load_json(json.loads(j), None, None, obj=self.rt_obj)


if __name__ == "__main__":
    unittest.main()
