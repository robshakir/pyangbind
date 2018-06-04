#!/usr/bin/env python

import unittest

from pyangbind.lib.xpathhelper import YANGPathHelper
from tests.base import PyangBindTestCase


class RPCTests(PyangBindTestCase):
    yang_files = ["rpc.yang"]
    split_class_dir = True
    pyang_flags = ["--use-xpathhelper", "--build-rpc"]

    def setUp(self):
        self.path_helper = YANGPathHelper()

    def test_set_input_argument(self):
        from bindings.rpc_rpc.check import check

        instance = check(path_helper=self.path_helper)

        allowed = True
        try:
            instance.input.argument = "test"
        except ValueError:
            allowed = False
        self.assertTrue(allowed)

    def test_set_output_arguments(self):
        from bindings.rpc_rpc.check_two import output

        instance = output.output(path_helper=self.path_helper)
        allowed = True
        try:
            instance.arg_one = 10
            instance.arg_two = 20
        except ValueError:
            allowed = False
        self.assertTrue(allowed)

    def test_set_input_arguments_inside_container(self):
        from bindings.rpc_rpc.check_three import check_three

        instance = check_three(path_helper=self.path_helper)
        allowed = True
        try:
            instance.input.arguments.arg_one = "test string"
            instance.input.arguments.arg_two = "another test string"
        except ValueError:
            allowed = False
        self.assertTrue(allowed)

    def test_set_output_arguments_with_multiple_containers(self):
        from bindings.rpc_rpc.check_four import check_four

        instance = check_four(path_helper=self.path_helper)
        allowed = True
        try:
            instance.output.arguments.arg_one = "test string"
            instance.output.arguments_two.arg_two = "another test string"
        except ValueError:
            allowed = False
        self.assertTrue(allowed)

    def set_input_and_output_arguments_on_a_single_rpc_check(self):
        from bindings.rpc_rpc.check_five import check_five

        instance = check_five(path_helper=self.path_helper)
        allowed = True
        try:
            instance.input.arguments.arg_one = "test string"
            instance.output.return_values.return_val = 10
        except ValueError:
            allowed = False
        self.assertTrue(allowed)

    def test_rpc_attributes_do_not_register_in_path_helper(self):
        from bindings.rpc_rpc.check import check

        instance = check(path_helper=self.path_helper)
        instance.input.argument = "test string"
        self.assertEqual(dict(self.path_helper.get_unique("/")), {})

    def test_set_input_argument_to_valid_leafref(self):
        from bindings import rpc
        from bindings.rpc_rpc.check_six import check_six

        base_instance = rpc(path_helper=self.path_helper)
        instance = check_six(path_helper=self.path_helper)

        base_instance.test.reference_target.append("six")
        allowed = True
        try:
            instance.input.argument = "six"
        except ValueError:
            allowed = False
        self.assertTrue(allowed)

    def test_set_input_argument_to_invalid_leafref(self):
        from bindings import rpc
        from bindings.rpc_rpc.check_six import check_six

        base_instance = rpc(path_helper=self.path_helper)
        instance = check_six(path_helper=self.path_helper)

        base_instance.test.reference_target.append("six")
        with self.assertRaises(ValueError):
            instance.input.argument = "fish"


if __name__ == "__main__":
    unittest.main()
