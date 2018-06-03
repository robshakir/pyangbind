#!/usr/bin/env python

from __future__ import unicode_literals, print_function
import pprint
import pyangbind.lib.pybindJSON as pbJ
import sbindings
import os

pp = pprint.PrettyPrinter(indent=4)

# Load an instance from file using PyBind's native JSON format
loaded_object = pbJ.load(os.path.join("json", "simple-instance.json"), sbindings, "simple_serialise")
pp.pprint(loaded_object.get(filter=True))

# Load an instance from a corresponding string using the native JSON format
string_to_load = open(os.path.join("json", "simple-instance.json"), "r")
string_to_load = string_to_load.read().replace("\n", "")
loaded_object_two = pbJ.loads(string_to_load, sbindings, "simple_serialise")
pp.pprint(loaded_object_two.get(filter=True))

# Load an instance from an IETF-JSON file
loaded_ietf_obj = pbJ.load_ietf(os.path.join("json", "simple-instance-ietf.json"), sbindings, "simple_serialise")
pp.pprint(loaded_ietf_obj.get(filter=True))

# Load an instance from an IETF-JSON string
string_to_load = open(os.path.join("json", "simple-instance-ietf.json"), "r")
string_to_load = string_to_load.read().replace("\n", "")

loaded_ietf_obj_two = pbJ.loads_ietf(string_to_load, sbindings, "simple_serialise")
pp.pprint(loaded_ietf_obj_two.get(filter=True))

# Load into an existing instance
from pyangbind.lib.serialise import pybindJSONDecoder
import json

# Create a new instance
existing_instance = sbindings.simple_serialise()
existing_instance.a_list.add("entry-one")
existing_instance.a_list.add("entry-two")

fn = os.path.join("json", "simple-instance-additional.json")
data_to_load = json.load(open(fn, "r"))
pybindJSONDecoder.load_json(data_to_load, None, None, obj=existing_instance)

pp.pprint(existing_instance.a_list.keys())
pp.pprint(existing_instance.get(filter=True))

# Serialise objects to JSON
print(pbJ.dumps(existing_instance, filter=True))
print(pbJ.dumps(existing_instance, filter=True, mode="ietf"))
print(pbJ.dumps(existing_instance.a_list, select={"the-key": "entry-one"}))
print(pbJ.dumps(existing_instance.a_list, select={"the-key": "entry-one"}, mode="ietf"))
