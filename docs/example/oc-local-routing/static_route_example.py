#!/usr/bin/env python

from __future__ import print_function, unicode_literals
from binding import openconfig_local_routing
import pyangbind.lib.pybindJSON as pybindJSON
import os

# Instantiate a copy of the pyangbind-kettle module
oclr = openconfig_local_routing()

# Add an entry to the static route list
rt = oclr.local_routes.static_routes.static.add("192.0.2.1/32")

# Set a tag for the route
rt.config.set_tag = 42

# Retrieve the tag value
print(rt.config.set_tag)

# Retrieve the tag value through the original object
print(oclr.local_routes.static_routes.static["192.0.2.1/32"].config.set_tag)

# Use the get() method to see the content of the classes
# using the filter=True keyword to get only elements that
# are not empty or the default
print(oclr.local_routes.static_routes.static["192.0.2.1/32"].get(filter=True))

# Add a set of next_hops
for nhop in [(0, "192.168.0.1"), (1, "10.0.0.1")]:
    nh = rt.next_hops.next_hop.add(nhop[0])
    nh.config.next_hop = nhop[1]

# Iterate through the next-hops added
for index, nh in rt.next_hops.next_hop.iteritems():
    print("%s: %s" % (index, nh.config.next_hop))

# Try and set an invalid tag type
try:
    rt.config.set_tag = "INVALID-TAG"
except ValueError as m:
    print("Cannot set tag: %s" % m)

# Dump the entire instance as JSON in PyangBind format
print(pybindJSON.dumps(oclr))

# Dump the static routes instance as JSON in IETF format
print(pybindJSON.dumps(oclr.local_routes, mode="ietf"))

# Load the "json/oc-lr.json" file into a new instance of
# "openconfig_local_routing". We import the module here, such that a new
# instance of the class can be created by the deserialisation code
import binding

new_oclr = pybindJSON.load(os.path.join("json", "oc-lr.json"), binding, "openconfig_local_routing")

# Manipulate the data loaded
print("Current tag: %d" % new_oclr.local_routes.static_routes.static["192.0.2.1/32"].config.set_tag)
new_oclr.local_routes.static_routes.static["192.0.2.1/32"].config.set_tag += 1
print("New tag: %d" % new_oclr.local_routes.static_routes.static["192.0.2.1/32"].config.set_tag)

# Load JSON into an existing class structure
from pyangbind.lib.serialise import pybindJSONDecoder
import json

ietf_json = json.load(open(os.path.join("json", "oc-lr_ietf.json"), "r"))
pybindJSONDecoder.load_ietf_json(ietf_json, None, None, obj=new_oclr.local_routes)

# Iterate through the classes - both the 192.0.2.1/32 prefix and 192.0.2.2/32
# prefix are now in the objects
for prefix, route in new_oclr.local_routes.static_routes.static.iteritems():
    print("Prefix: %s, tag: %d" % (prefix, route.config.set_tag))
