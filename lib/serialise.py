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

class pybindJSONUpdateError(Exception):
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
          return True
        else:
          return False
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
    elif isinstance(obj, str) or isinstance(obj, unicode):
      return unicode(obj)
    return json.JSONEncoder.default(self, obj)

class pybindJSONDecoder(object):
  def load_json(self, d, parent, yang_base, obj=None, path_helper=None, update=False, extmethods=None):
    if update and not obj:
      raise pybindJSONUpdateError("can't update a missing object")

    if obj is None:
      # we need to find the class to create, as one has not been supplied.
      base_mod_cls = getattr(parent, safe_name(yang_base))
      tmp = base_mod_cls(path_helper=False)

      if path_helper is not None:
        # check that this path doesn't already exist in the
        # tree, otherwise we create a duplicate.
        existing_objs = path_helper.get(tmp._path())
        if len(existing_objs) == 0:
          obj = base_mod_cls(path_helper=path_helper, extmethods=extmethods)
        elif len(existing_objs) == 1:
          obj = existing_objs[0]
        else:
          raise pybindJSONUpdateError('update was attempted to a node that was not unique')
      else:
        # in this case, we cannot check for an existing object
        obj = base_mod_class(path_helper=path_helper, extmethods=extmethods)

    for key in d:
      child = getattr(obj, "_get_%s" % safe_name(key), None)
      if child is None:
        raise AttributeError("JSON object contained a key that did not exist (%s)" % (key))
      chobj = child()
      set_via_stdmethod = True
      pybind_attr = getattr(child(), '_pybind_generated_by', None)
      if pybind_attr in ["container"]:
        # the child is a container, so call this method for it
        self.load_json(d[key], chobj, yang_base, obj=chobj)
        set_via_stdmethod = False
      elif pybind_attr in ["YANGListType", "list"]:
        # we need to add each key to the list and then skip a level in the
        # JSON hierarchy
        for child_key in d[key]:
          if not child_key in chobj:
            chobj.add(child_key)
          parent = chobj[child_key]
          self.load_json(d[key][child_key], parent, yang_base, obj=parent)
          set_via_stdmethod = False
      elif pybind_attr in ["RestrictedClassType","TypedListType","ReferencePathType"]:
        # normal but valid types - which use the std set method
        pass
      elif pybind_attr is None:
        # not a pybind attribute at all - keep using the std set method
        pass
      else:
        raise pybindJSONUpdateError("unknown pybind type when loading JSON: %s" % pybind_attr)
      if set_via_stdmethod:
        # simply get the set method and then set the value of the leaf
        set_method = getattr(obj, "_set_%s" % safe_name(key))
        set_method(d[key])
    return obj

