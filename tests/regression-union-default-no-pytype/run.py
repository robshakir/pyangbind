#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class UnionDefaultMissingPytypeRegressionTests(PyangBindTestCase):
    yang_files = ["regression-union-default-no-pytype.yang"]

    def setUp(self):
        self.instance = self.bindings.regression_union_default_no_pytype()

    def test_generation_succeeds_and_default_is_enum_string(self):
        self.assertEqual(self.instance.configure.burst_limit, 0)
        self.assertEqual(self.instance.configure.burst_limit._default, "auto")


if __name__ == "__main__":
    unittest.main()
