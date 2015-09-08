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
from yangtypes import safe_name
from types import ModuleType

class pybindJSONIOError(Exception):
  pass

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
                nd[k] = self.default(d[k])
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
    if isinstance(obj, list):
      nlist = []
      for elem in obj:
        nlist.append(self.default(elem))
      return nlist

    if hasattr(obj, "_pybind_base_class"):
      pybc = getattr(obj, "_pybind_base_class")
      pybo = obj

      if pybc in ["lib.yangtypes.RestrictedClass"]:
        pybc = getattr(obj, "_restricted_class_base")[0]

      if pybc in ["numpy.uint8", "numpy.uint16", "numpy.uint32", "numpy.uint64", "numpy.int8", "numpy.int16", "numpy.int32", "numpy.int64"]:
        return int(obj)
      elif pybc in ["lib.yangtypes.ReferencePathType",]:
        return str(obj)
      elif pybc in ["lib.yangtypes.RestrictedPrecisionDecimal"]:
        return float(obj)
      elif pybc in ["bitarray.bitarray"]:
        return obj.to01()
      elif pybc in ["lib.yangtypes.YANGBool"]:
        if obj:
          return "true"
        else:
          return "false"
      elif pybc in ["unicode"]:
        return unicode(obj)
      else:
        print dir(pybc)
        print pybc.__class__
        raise AttributeError("this was an unmapped pyangbind class... (%s)" % pybc)
    elif isinstance(obj, Decimal):
      return float(obj)
    elif type(obj) in [int, numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint64, numpy.int8, numpy.int16, numpy.int32, numpy.int64]:
      return int(obj)
    elif isinstance(obj, str):
      return unicode(obj)
    return json.JSONEncoder.default(self, obj)

class pybindJSONDecoder(object):
  def load_json(self, d, parent, yang_module, obj=False, path_helper=None):
    if not obj:
      base_mod_cls = getattr(parent, safe_name(yang_module))
      obj = base_mod_cls(path_helper=path_helper)
      for cls in d:
        tmod = getattr(obj, safe_name(cls))
        if isinstance(tmod, ModuleType):
          pcls = getattr(tmod, safe_name(cls))
        else:
          pcls = tmod
        pybind_attr = getattr(pcls, "_pybind_generated_by", False)
        standard_class = True
        if pybind_attr:
          # check that this isn't a list otherwise we need to call
          # the method differently
          if pybind_attr in ["YANGListType", "list"]:
            attr = getattr(obj, "_get_%s" % safe_name(cls))
            for child_key in d[cls]:
              attr().add(child_key)
              parent = attr()[child_key]
              standard_class = False
              self.load_json(d[cls][child_key], parent, yang_module, obj=obj)
        if standard_class:
          self.load_json(d[cls], pcls, yang_module, obj=obj)
    else:
      for key in d:
        set_via_method = False
        attr = getattr(parent, "_get_%s" % safe_name(key))
        pybind_attr = getattr(attr(), "_pybind_generated_by", False)
        if pybind_attr:
          if pybind_attr in ["YANGListType", "list"]:
            for child_key in d[key]:
              attr().add(child_key)
              parent = attr()[child_key]
              self.load_json(d[key][child_key], parent, yang_module, obj=obj)
          elif pybind_attr in ["RestrictedClassType","TypedListType","ReferencePathType"]:
            set_via_method = True
          elif pybind_attr == "container":
            self.load_json(d[key], attr(), yang_module, obj=obj)
          else:
            raise AttributeError("some unhandled pybind class on load (%s)" % pybind_attr)
        else:
          set_via_method = True
        if set_via_method:
          set_method = getattr(parent, "_set_%s" % safe_name(key))
          set_method(d[key])
    return obj