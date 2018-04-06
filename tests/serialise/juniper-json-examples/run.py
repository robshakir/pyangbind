#!/usr/bin/env python
from __future__ import unicode_literals

import json
import os.path
import unittest

from pyangbind.lib.serialise import pybindJSONDecoder
from pyangbind.lib.xpathhelper import YANGPathHelper
from tests.base import PyangBindTestCase


class JuniperJSONTests(PyangBindTestCase):
  pyang_flags = ['-p %s' % os.path.join(os.path.dirname(__file__), "include")]
  yang_files = [os.path.join('openconfig', 'openconfig-bgp.yang')]
  split_class_dir = True
  module_name = 'ocbind'

  remote_yang_files = [
    {
      'local_path': 'include',
      'remote_prefix': 'https://raw.githubusercontent.com/robshakir/yang/master/standard/ietf/RFC/',
      'files': [
        'ietf-inet-types.yang',
        'ietf-yang-types.yang',
        'ietf-interfaces.yang',
      ]
    },
    {
      'local_path': 'include',
      'remote_prefix': 'https://raw.githubusercontent.com/openconfig/public/master/release/models/',
      'files': [
        'policy/openconfig-policy-types.yang',
        'openconfig-extensions.yang',
        'types/openconfig-types.yang',
        'types/openconfig-inet-types.yang',
        'types/openconfig-yang-types.yang',
        'bgp/openconfig-bgp-types.yang',
      ]
    },
    {
      'local_path': 'openconfig',
      'remote_prefix': 'https://raw.githubusercontent.com/openconfig/public/master/release/models/',
      'files': [
        'bgp/openconfig-bgp-common-multiprotocol.yang',
        'bgp/openconfig-bgp-common-structure.yang',
        'bgp/openconfig-bgp-common.yang',
        'bgp/openconfig-bgp-global.yang',
        'bgp/openconfig-bgp-neighbor.yang',
        'bgp/openconfig-bgp-peer-group.yang',
        'bgp/openconfig-bgp-policy.yang',
        'bgp/openconfig-bgp-errors.yang',
        'bgp/openconfig-bgp.yang',
        'policy/openconfig-routing-policy.yang',
        'interfaces/openconfig-interfaces.yang',
        'types/openconfig-yang-types.yang',
        'types/openconfig-inet-types.yang',
      ]
    }
  ]

  def setUp(self):
    self.yang_helper = YANGPathHelper()

  def test_load_global_config(self):
    expected_json = {
      "bgp": {
        "global": {
           "confederation": {
              "config": {
                 "identifier": 65517,
                 "member-as": [
                    65518,
                    65519,
                    65520
                 ]
              }
           }
        }
      }
    }
    bgp_global_ex = json.load(open(os.path.join(os.path.dirname(__file__), "json", "bgp-global-ex.json"), 'r'))
    actual_json = pybindJSONDecoder.load_ietf_json(
      bgp_global_ex['configuration'],
      self.ocbind,
      'openconfig_bgp',
      path_helper=self.yang_helper
    ).get(filter=True)
    self.assertEqual(actual_json, expected_json, "Invalid JSON loaded for global config")

  def test_load_neighbor_list(self):
    expected_json = {
      "bgp": {
        "neighbors": {
           "neighbor": {
              "13.13.13.13": {
                 "neighbor-address": "13.13.13.13",
                 "config": {
                    "peer-group": "g1"
                 }
              },
              "12.12.12.12": {
                 "neighbor-address": "12.12.12.12",
                 "config": {
                    "peer-group": "g1"
                 }
              }
           }
        }
      }
    }
    bgp_neighbor_list = json.load(
      open(os.path.join(os.path.dirname(__file__), "json", "bgp-neighbor-list-ex.json"), 'r'))
    actual_json = pybindJSONDecoder.load_ietf_json(
      bgp_neighbor_list['configuration'],
      self.ocbind,
      'openconfig_bgp',
      path_helper=self.yang_helper
    ).get(filter=True)
    self.assertEqual(actual_json, expected_json, "Invalid JSON returned when loading neighbor list")

  def test_load_graceful_restart(self):
    expected_json = {
      "bgp": {
        "neighbors": {
           "neighbor": {
              "12.12.12.12": {
                 "config": {
                    "peer-group": "g1"
                 },
                 "neighbor-address": "12.12.12.12"
              },
              "13.13.13.13": {
                 "neighbor-address": "13.13.13.13",
                 "config": {
                    "peer-group": "g2"
                 }
              }
           }
        }
      }
    }
    graceful_restart_neighbors = json.load(
      open(os.path.join(os.path.dirname(__file__), "json", "bgp-gr-ex.json"), 'r')
    )
    actual_json = pybindJSONDecoder.load_ietf_json(
      graceful_restart_neighbors['configuration'],
      self.ocbind,
      'openconfig_bgp',
      path_helper=self.yang_helper
    ).get(filter=True)
    self.assertEqual(actual_json, expected_json, "Graceful restart example was not loaded correctly.")

  def test_load_graceful_restart_metadata(self):
    graceful_restart_neighbors = json.load(
      open(os.path.join(os.path.dirname(__file__), "json", "bgp-gr-ex.json"), 'r')
    )
    neighbors_instance = pybindJSONDecoder.load_ietf_json(
      graceful_restart_neighbors['configuration'],
      self.ocbind,
      'openconfig_bgp',
      path_helper=self.yang_helper
    )
    self.assertEqual(
      neighbors_instance.bgp.neighbors.neighbor["12.12.12.12"]._metadata,
      {'inactive': True},
      "Metadata for graceful restart example was not loaded correctly."
    )

  def test_load_deactivated(self):
    expected_json = {
      "bgp": {
        "global": {
          "config": {
            "router-id": "10.10.10.10",
          }
        }
      }
    }
    deactivated = json.load(
      open(os.path.join(os.path.dirname(__file__), "json", "bgp-deactivated-config-ex.json"), 'r')
    )
    actual_json = pybindJSONDecoder.load_ietf_json(
      deactivated['configuration'],
      self.ocbind,
      'openconfig_bgp',
      path_helper=self.yang_helper
    ).get(filter=True)
    self.assertEqual(actual_json, expected_json, "Router ID configuration example not loaded correctly.")

  def test_load_deactivated_metadata(self):
    deactivated = json.load(
      open(os.path.join(os.path.dirname(__file__), "json", "bgp-deactivated-config-ex.json"), 'r')
    )
    deactivated_instance = pybindJSONDecoder.load_ietf_json(
      deactivated['configuration'],
      self.ocbind,
      'openconfig_bgp',
      path_helper=self.yang_helper
    )
    self.assertTrue(
      deactivated_instance.bgp.global_.config.router_id._metadata['inactive'],
      "Metadata for router-id element not set correctly."
    )


if __name__ == '__main__':
  unittest.main()
