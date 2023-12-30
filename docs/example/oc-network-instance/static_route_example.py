#!/usr/bin/env python

from __future__ import print_function, unicode_literals
from binding import openconfig_network_instance
import pyangbind.lib.pybindJSON as pybindJSON
import os

# Instantiate a copy of the pyangbind-kettle module and add a network instance.
ocni = openconfig_network_instance()
ocni.network_instances.network_instance.add('a')
ocni.network_instances.network_instance['a'].protocols.protocol.add(identifier='STATIC', name='DEFAULT')

# Add an entry to the static route list
rt = ocni.network_instances.network_instance['a'].protocols.protocol['STATIC DEFAULT'].static_routes.static.add("192.0.2.1/32")

# Set a tag for the route
rt.config.set_tag = 42

# Retrieve the tag value
print(rt.config.set_tag)

# Retrieve the tag value through the original object
print(ocni.network_instances.network_instance['a'].protocols.protocol['STATIC DEFAULT'].static_routes.static["192.0.2.1/32"].config.set_tag)

# Use the get() method to see the content of the classes
# using the filter=True keyword to get only elements that
# are not empty or the default
print(ocni.network_instances.network_instance['a'].protocols.protocol['STATIC DEFAULT'].static_routes.static["192.0.2.1/32"].get(filter=True))

# Add a set of next_hops
for nhop in [(0, "192.168.0.1"), (1, "10.0.0.1")]:
    nh = rt.next_hops.next_hop.add(nhop[0])
    nh.config.next_hop = nhop[1]

# Iterate through the next-hops added
for index, nh in rt.next_hops.next_hop.items():
    print("%s: %s" % (index, nh.config.next_hop))

# Try and set an invalid tag type
try:
    rt.config.set_tag = "INVALID-TAG"
except ValueError as m:
    print("Cannot set tag: %s" % m)

# Dump the entire instance as JSON in PyangBind format
print(pybindJSON.dumps(ocni, indent=2))

# Dump the static routes instance as JSON in IETF format
print(pybindJSON.dumps(ocni.network_instances.network_instance['a'].protocols.protocol['STATIC DEFAULT'], mode='ietf', indent=2))

# Load the "json/oc-ni.json" file into a new instance of
# "openconfig_network_instance". We import the module here, such that a new
# instance of the class can be created by the deserialisation code.
# Note that you may need to provide the absolute path to oc-ni.json.
import binding

new_ocni = pybindJSON.load(os.path.join("json", "oc-ni.json"), binding, "openconfig_network_instance")

# Manipulate the data loaded
print("Current tag: %d" % new_ocni.network_instances.network_instance['a'].protocols.protocol['STATIC DEFAULT'].static_routes.static['192.0.2.1/32'].config.set_tag)
new_ocni.network_instances.network_instance['a'].protocols.protocol['STATIC DEFAULT'].static_routes.static['192.0.2.1/32'].config.set_tag += 1
print("New tag: %d" % new_ocni.network_instances.network_instance['a'].protocols.protocol['STATIC DEFAULT'].static_routes.static['192.0.2.1/32'].config.set_tag)

# Load JSON into an existing class structure
from pyangbind.lib.serialise import pybindJSONDecoder
import json

# Provide absolute path to oc-ni_ietf.json if needed.
ietf_json = json.load(open(os.path.join("json", "oc-ni_ietf.json"), "r"))
pybindJSONDecoder.load_ietf_json(ietf_json, None, None, obj=new_ocni.network_instances.network_instance['a'].protocols.protocol['STATIC DEFAULT'])

# Iterate through the classes - both the 192.0.2.1/32 prefix and 192.0.2.2/32
# prefix are now in the objects
for prefix, route in new_ocni.network_instances.network_instance['a'].protocols.protocol['STATIC DEFAULT'].static_routes.static.items():
    print("Prefix: %s, tag: %d" % (prefix, route.config.set_tag))
