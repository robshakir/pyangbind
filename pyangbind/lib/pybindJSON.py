"""
Copyright 2015, Rob Shakir (rjs@jive.com, rjs@rob.sh)

This project has been supported by:
          * Jive Communications, Inc.
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
"""
from .serialise import pybindJSONEncoder, pybindJSONDecoder, pybindJSONIOError
from .serialise import pybindIETFJSONEncoder
import json
import copy


def remove_path(tree, path):
  this_part = path.pop(0)
  if len(path) == 0:
    try:
      del tree[this_part]
      return tree
    except KeyError:
      # ignore missing dictionary key
      pass
  else:
    try:
      tree[this_part] = remove_path(tree[this_part], path)
    except KeyError:
      pass
  return tree


def loads(d, parent_pymod, yang_base, path_helper=None, extmethods=None,
          overwrite=False):
  # This check is not really logical - since one would expect 'd' to be
  # a string, given that this is loads. However, a previous issue meant
  # that this really expected a dict, so this check simply makes sure
  # that if the user really did give us a string, we're happy with that
  # without breaking other code.
  if isinstance(d, unicode) or isinstance(d, str):
    d = json.loads(d)
  return pybindJSONDecoder.load_json(d, parent_pymod, yang_base,
          path_helper=path_helper, extmethods=extmethods, overwrite=overwrite)


def loads_ietf(d, parent_pymod, yang_base, path_helper=None,
                extmethods=None, overwrite=False):
  # Same as above, to allow for load_ietf to work the same way
  if isinstance(d, unicode) or isinstance(d, str):
    d = json.loads(d)
  return pybindJSONDecoder.load_ietf_json(d, parent_pymod, yang_base,
          path_helper=path_helper, extmethods=extmethods, overwrite=overwrite)


def load(fn, parent_pymod, yang_module, path_helper=None, extmethods=None,
             overwrite=False):
  try:
    f = json.load(open(fn, 'r'))
  except IOError, m:
    raise pybindJSONIOError("could not open file to read: %s" % m)
  return loads(f, parent_pymod, yang_module, path_helper=path_helper,
                extmethods=extmethods, overwrite=overwrite)


def load_ietf(fn, parent_pymod, yang_module, path_helper=None,
              extmethods=None, overwrite=False):
  try:
    f = json.load(open(fn, 'r'))
  except IOError, m:
    raise pybindJSONIOError("Could not open file to read: %s" % m)
  return loads_ietf(f, parent_pymod, yang_module, path_helper,
            extmethods=extmethods, overwrite=overwrite)


def dumps(obj, indent=4, filter=True, skip_subtrees=[], select=False,
            mode="default"):
  def lookup_subdict(dictionary, key):
    if not isinstance(key, list):
      raise AttributeError('keys should be a list')
    unresolved_dict = {}
    for k, v in dictionary.iteritems():
      if ":" in k:
        k = k.split(":")[1]
      unresolved_dict[k] = v

    if not key[0] in unresolved_dict:
      raise KeyError("requested non-existent key (%s)" % key[0])
    if len(key) == 1:
      return unresolved_dict[key[0]]
    current = key.pop(0)
    return lookup_subdict(dictionary[current], key)

  if not isinstance(skip_subtrees, list):
    raise AttributeError('the subtrees to be skipped should be a list')
  if mode == 'ietf':
    tree = pybindIETFJSONEncoder.generate_element(obj, flt=filter)
  else:
    tree = obj.get(filter=filter)
  for p in skip_subtrees:
    pp = p.split("/")[1:]
    # Iterate through the skip path and the object's own path to determine
    # whether they match, then skip the relevant subtrees.
    match = True
    trimmed_path = copy.deepcopy(pp)
    for i, j in zip(obj._path(), pp):
      # paths may have attributes in them, but the skip dictionary does
      # not, so we ensure that the object's absolute path is attribute
      # free,
      if "[" in i:
        i = i.split("[")[0]
      if not i == j:
        match = False
        break
      trimmed_path.pop(0)

    if match and len(trimmed_path):
      tree = remove_path(tree, trimmed_path)

  if select:
    key_del = []
    for t in tree:
      keep = True
      for k, v in select.iteritems():
        if mode == 'default' or isinstance(tree, dict):
          if keep and not \
                unicode(lookup_subdict(tree[t], k.split("."))) == unicode(v):
            keep = False
        else:
          # handle ietf case where we have a list and might have namespaces
          if keep and not \
                unicode(lookup_subdict(t, k.split("."))) == unicode(v):
            keep = False
      if not keep:
        key_del.append(t)
    if mode == 'default' or isinstance(tree, dict):
      for k in key_del:
        if mode == 'default':
          del tree[k]
    else:
      for i in key_del:
        tree.remove(i)

  if mode == "ietf":
    cls = pybindIETFJSONEncoder
  else:
    cls = pybindJSONEncoder

  return json.dumps(tree, cls=cls, indent=indent)


def dump(obj, fn, indent=4, filter=True, skip_subtrees=[],
         mode="default"):
  try:
    fh = open(fn, 'w')
  except IOError, m:
    raise pybindJSONIOError("could not open file for writing: %s" % m)
  fh.write(dumps(obj, indent=indent, filter=filter,
              skip_subtrees=skip_subtrees, mode=mode))
  fh.close()