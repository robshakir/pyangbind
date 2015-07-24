"""
Copyright 2015  Rob Shakir (rjs@rob.sh)

This project has been supported by:
          * BT plc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

serialise:
  * module containing methods to serialise pyangbind class hierarchie
    to various data encodings. XML and/or JSON as the primary examples.
"""

import json
import numpy
from collections import OrderedDict
from decimal import Decimal

class pybindJSONEncoder(json.JSONEncoder):
  def default(self, obj):
    # if isinstance(foo,bar):
    #  return <encoded type>
    print "type %s" % (type(obj))
    if hasattr(obj, "_pybind_base_class"):
      print "%s -> %s - had attr %s" % (obj, type(obj), getattr(obj, "_pybind_base_class"))
      pybc = getattr(obj, "_pybind_base_class")

      if pybc in ["lib.yangtypes.RestrictedClass"]:
        pybc = getattr(obj, "_restricted_class_base")

      if pybc in ["numpy.uint8", "numpy.uint16", "numpy.uint32", "numpy.uint64", "numpy.int8", "numpy.int16", "numpy.int32", "numpy.int64"]:
        return int(obj)
      elif pybc in ["lib.yangtypes.ReferencePathType",]:
        return str(obj)
      elif pybc in ["lib.yangtypes.RestrictedPrecisionDecimal"]:
        return float(obj)

      else:
        print dir(pybc)
        print pybc.__class__
        raise AttributeError("this was an unmapped pyangbind class... (%s)" % pybc)
    elif isinstance(obj, Decimal):
      return float(obj)
    elif type(obj) in [numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint64, numpy.int8, numpy.int16, numpy.int32, numpy.int64]:
      return int(obj)
    # elif isinstance(obj, OrderedDict):
    #   new_dict = {}
    #   index = 0
    #   for k,v in obj.iteritems():
    #     new_dict[self.default(k)] = self.default(v)
    #     if not type(new_dict[self.default(k)]) in [dict, OrderedDict]:
    #       raise ValueError("A YANG OrderedDict should be a list")
    #     new_dict[self.default(k)]['__yang_order'] = index
    #     index += 1
    #   return "{" + ",".join([self.encode(k) + ":" + self.encode(v) for k,v in new_dict.iteritems()]) + "}"
    return json.JSONEncoder.default(self, obj)


