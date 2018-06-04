#!/usr/bin/env python

import unittest

from tests.base import PyangBindTestCase


class OpenconfigBGPJuniperTests(PyangBindTestCase):
    yang_files = ["openconfig-bgp-juniper.yang"]

    global_config = {"my_as": 2856}
    peer_group_list = ["groupA", "groupB"]
    peers = [
        ("1.1.1.1", "groupA", 3741),
        ("1.1.1.2", "groupA", 5400),
        ("1.1.1.3", "groupA", 29636),
        ("2.2.2.2", "groupB", 12767),
    ]

    def setUp(self):
        self.bgp_obj = self.bindings.openconfig_bgp_juniper()

        # Pre-populate our data
        self.bgp_obj.juniper_config.bgp.global_.as_ = self.global_config["my_as"]
        for peer_group in self.peer_group_list:
            self.bgp_obj.juniper_config.bgp.peer_group.add(peer_group)

        for peer in self.peers:
            self.bgp_obj.juniper_config.bgp.peer_group[peer[1]].neighbor.add(peer[0])
            self.bgp_obj.juniper_config.bgp.peer_group[peer[1]].neighbor[peer[0]].peer_as = peer[2]

    def test_set_unknown_element(self):
        allowed = True
        try:
            self.bgp_obj.system = False
        except AttributeError:
            allowed = False
        self.assertFalse(allowed, "Trying to set a missing container did not result in an attribute error")

    def test_get(self):
        self.assertEqual(
            self.bgp_obj.get(),
            {
                "juniper-config": {
                    "bgp": {
                        "global": {"as": "2856"},
                        "peer-group": {
                            "groupA": {
                                "group-name": "groupA",
                                "neighbor": {
                                    "1.1.1.1": {"neighbor-name": "1.1.1.1", "peer-as": "3741"},
                                    "1.1.1.2": {"neighbor-name": "1.1.1.2", "peer-as": "5400"},
                                    "1.1.1.3": {"neighbor-name": "1.1.1.3", "peer-as": "29636"},
                                },
                                "peer-type": "",
                            },
                            "groupB": {
                                "group-name": "groupB",
                                "neighbor": {"2.2.2.2": {"neighbor-name": "2.2.2.2", "peer-as": "12767"}},
                                "peer-type": "",
                            },
                        },
                    }
                }
            },
            "Unfiltered get response did not match",
        )

    def test_filtered_get(self):
        self.assertEqual(
            self.bgp_obj.get(filter=True),
            {
                "juniper-config": {
                    "bgp": {
                        "global": {"as": "2856"},
                        "peer-group": {
                            "groupA": {
                                "group-name": "groupA",
                                "neighbor": {
                                    "1.1.1.1": {"neighbor-name": "1.1.1.1", "peer-as": "3741"},
                                    "1.1.1.2": {"neighbor-name": "1.1.1.2", "peer-as": "5400"},
                                    "1.1.1.3": {"neighbor-name": "1.1.1.3", "peer-as": "29636"},
                                },
                            },
                            "groupB": {
                                "group-name": "groupB",
                                "neighbor": {"2.2.2.2": {"neighbor-name": "2.2.2.2", "peer-as": "12767"}},
                            },
                        },
                    }
                }
            },
            "filtered get response did not match",
        )


if __name__ == "__main__":
    unittest.main()
