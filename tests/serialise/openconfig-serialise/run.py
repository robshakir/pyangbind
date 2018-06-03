#!/usr/bin/env python

import json
import os.path
import unittest

import regex

from pyangbind.lib.pybindJSON import dumps
from pyangbind.lib.serialise import pybindIETFJSONEncoder, pybindJSONEncoder
from pyangbind.lib.xpathhelper import YANGPathHelper
from pyangbind.lib.yangtypes import YANGBool
from tests.base import PyangBindTestCase

TESTNAME = "json-serialise"


class OpenconfigSerialiseTests(PyangBindTestCase):
    maxDiff = None
    split_class_dir = True
    module_name = "ocbind"
    yang_files = [os.path.join(os.path.dirname(__file__), "openconfig", "openconfig-interfaces.yang")]
    pyang_flags = ["--use-xpathhelper", "-p %s" % os.path.join(os.path.dirname(__file__), "include")]

    remote_yang_files = [
        {
            "local_path": "include",
            "remote_prefix": "https://raw.githubusercontent.com/openconfig/public/master/release/models/",
            "files": [
                "openconfig-extensions.yang",
                "types/openconfig-types.yang",
                "types/openconfig-yang-types.yang",
                "types/openconfig-inet-types.yang",
            ],
        },
        {
            "local_path": "include",
            "remote_prefix": "https://raw.githubusercontent.com/robshakir/yang/master/standard/ietf/RFC/",
            "files": ["ietf-inet-types.yang", "ietf-yang-types.yang"],
        },
        {
            "local_path": "openconfig",
            "remote_prefix": "https://raw.githubusercontent.com/openconfig/public/master/release/models/",
            "files": ["interfaces/openconfig-interfaces.yang"],
        },
    ]

    def setUp(self):
        self.yang_helper = YANGPathHelper()

    def test_json_generation(self):
        json_dir = os.path.join(os.path.dirname(__file__), "json")
        for file_name in os.listdir(json_dir):
            with self.subTest(json_file=file_name), open(os.path.join(json_dir, file_name), "r") as file_handle:
                parameters = regex.sub(
                    "interfaces\_ph:(?P<pathhelper>[a-zA-Z]+)\-flt:(?P<filter>[a-zA-Z]+)\-m:(?P<mode>[a-zA-Z]+)\.json",
                    "\g<pathhelper>||\g<filter>||\g<mode>",
                    file_name,
                ).split("||")
                path_helper, config_filter, mode = (YANGBool(parameters[0]), YANGBool(parameters[1]), parameters[2])
                if path_helper:
                    instance = self.ocbind.openconfig_interfaces(path_helper=self.yang_helper)
                else:
                    instance = self.ocbind.openconfig_interfaces()

                instance.interfaces.interface.add("eth0")

                expected_json = json.load(file_handle)
                actual_json = json.loads(dumps(instance, filter=bool(config_filter), mode=mode))

                self.assertEqual(
                    expected_json, actual_json, "Generated JSON did not match expected object for %s" % file_name
                )

    def test_pybind_ietf_json_encoder_serialisation_with_path_helper(self):
        instance = self.ocbind.openconfig_interfaces(path_helper=self.yang_helper)
        instance.interfaces.interface.add("eth0")

        passed = True
        try:
            json.loads(json.dumps(pybindIETFJSONEncoder.generate_element(instance), cls=pybindIETFJSONEncoder))
        except Exception:
            passed = False

        self.assertTrue(passed, "Serialisation test for object with pybindIETFJSONEncoder threw an error")

    def test_pybind_ietf_json_encoder_serialisation_without_path_helper(self):
        instance = self.ocbind.openconfig_interfaces()
        instance.interfaces.interface.add("eth0")

        passed = True
        try:
            json.loads(json.dumps(pybindIETFJSONEncoder.generate_element(instance), cls=pybindIETFJSONEncoder))
        except Exception:
            passed = False

        self.assertTrue(passed, "Serialisation test for object with pybindIETFJSONEncoder threw an error")

    def test_direct_json_serialisation_of_instance_with_path_helper(self):
        instance = self.ocbind.openconfig_interfaces(path_helper=self.yang_helper)
        instance.interfaces.interface.add("eth0")

        passed = True
        try:
            json.loads(json.dumps(instance, cls=pybindJSONEncoder))
        except Exception:
            passed = False

        self.assertTrue(passed)

    def test_direct_json_serialisation_of_instance_without_path_helper(self):
        instance = self.ocbind.openconfig_interfaces()
        instance.interfaces.interface.add("eth0")

        passed = True
        try:
            json.loads(json.dumps(instance, cls=pybindJSONEncoder))
        except Exception:
            passed = False

        self.assertTrue(passed)


if __name__ == "__main__":
    unittest.main()
