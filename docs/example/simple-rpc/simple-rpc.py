#!/usr/bin/env python

from __future__ import print_function, unicode_literals
from rbindings.simple_rpc_rpc.test.input import input
from rbindings.simple_rpc_rpc.test.output import output
from pyangbind.lib.serialise import pybindJSONDecoder
from pyangbind.lib.pybindJSON import dumps
import pprint
import os
import json

pp = pprint.PrettyPrinter(indent=4)

# Create an input instance
rpc_input = input()
rpc_input.input_container.argument_one = "test_call"
rpc_input.input_container.argument_two = 32
print(dumps(rpc_input, mode="ietf"))

# Load an output from IETF JSON
rpc_output = output()
fn = os.path.join("json", "rpc-output.json")
json_obj = json.load(open(fn, "r"))
pybindJSONDecoder.load_ietf_json(json_obj, None, None, obj=rpc_output)
print(rpc_output.response_id)

pp.pprint(rpc_output.get(filter=True))
