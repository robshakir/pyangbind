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
  def _preprocess_element(self, d):
      nd = {}
      if isinstance(d, OrderedDict) or isinstance(d, dict):
          index = 0
          for k in d:
              if isinstance(d[k], dict) or isinstance(d[k], OrderedDict):
                  nd[k] = self._preprocess_element(d[k])
                  if isinstance(d, OrderedDict):
                      nd[k]['__yang_order'] = index
              else:
                  nd[k] = d[k]
              # if we wanted to do this as per draft-ietf-netmod-yang-metadata
              # then the encoding is like this
              #if not "@%s" % k in nd:
              #  nd["@%s" % k] = {}
              #  nd["@%s" % k]['order'] = index
              # this has the downside that iterating over the dict gives you
              # some elements that do not really exist - there is a need to
              # exclude all elements that begin with "@"
              index += 1
      else:
          nd = d
      return nd

  def encode(self, obj):
    return json.JSONEncoder.encode(self, self._preprocess_element(obj))

  def default(self, obj):
    # if isinstance(foo,bar):
    #  return <encoded type>
    #print "%s->type %s" % (obj, type(obj))
    #print dir(obj)
    if hasattr(obj, "_pybind_base_class"):
      #print "%s -> %s - had attr %s" % (obj, type(obj), getattr(obj, "_pybind_base_class"))
      pybc = getattr(obj, "_pybind_base_class")

      if pybc in ["lib.yangtypes.RestrictedClass"]:
        pybc = getattr(obj, "_restricted_class_base")

      if pybc in ["numpy.uint8", "numpy.uint16", "numpy.uint32", "numpy.uint64", "numpy.int8", "numpy.int16", "numpy.int32", "numpy.int64"]:
        return int(obj)
      elif pybc in ["lib.yangtypes.ReferencePathType",]:
        return str(obj)
      elif pybc in ["lib.yangtypes.RestrictedPrecisionDecimal"]:
        return float(obj)
      elif pybc in ["bitarray.bitarray"]:
        return obj.to01()
      else:
        print dir(pybc)
        print pybc.__class__
        raise AttributeError("this was an unmapped pyangbind class... (%s)" % pybc)
    elif isinstance(obj, Decimal):
      return float(obj)
    elif type(obj) in [numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint64, numpy.int8, numpy.int16, numpy.int32, numpy.int64]:
      return int(obj)
    return json.JSONEncoder.default(self, obj)


