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
from serialise import pybindJSONEncoder, pybindJSONDecoder, pybindJSONIOError
import json

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


def loads(d, parent_pymod, yang_base, path_helper=None, extmethods=None, overwrite=False):
  return pybindJSONDecoder().load_json(d, parent_pymod, yang_base, path_helper=path_helper, extmethods=extmethods, overwrite=overwrite)

def dumps(obj, indent=4, filter=True, skip_subtrees=[],select=False):
  def lookup_subdict(dictionary, key):
    if not isinstance(key, list):
      raise AttributeError('keys should be a list')
    if not key[0] in dictionary:
      raise KeyError("requested non-existent key (%s)" % key[0])
    if len(key) == 1:
      return dictionary[key[0]]
    current = key.pop(0)
    return lookup_subdict(dictionary[current], key)

  if not isinstance(skip_subtrees, list):
    raise AttributeError('the subtrees to be skipped should be a list')
  tree = obj.get(filter=filter)
  for p in skip_subtrees:
    pp = p.split("/")[1:]
    tree = remove_path(tree, pp)
  if select:
    key_del = []
    for t in tree:
      keep = True
      for k, v in select.iteritems():
        if keep and not unicode(lookup_subdict(tree[t], k.split("."))) == unicode(v):
          keep = False
      if not keep:
        key_del.append(t)
    for k in key_del:
      del tree[k]
  return json.dumps(tree,cls=pybindJSONEncoder, indent=indent)

def dump(obj, fn, indent=4, filter=True, skip_subtrees=[]):
  try:
    fh = open(fn, 'w')
  except IOError, m:
    raise pybindJSONIOError("could not open file for writing: %s" % m)
  fh.write(dumps(obj, indent=indent, filter=filter, skip_subtrees=skip_subtrees))
  fh.close()

def load(fn, parent_pymod, yang_module, path_helper=None, extmethods=None, overwrite=False):
  try:
    f = json.load(open(fn, 'r'))
  except IOError, m:
    raise pybindJSONIOError("could not open file to read")
  return loads(f, parent_pymod, yang_module, path_helper=path_helper, extmethods=extmethods, overwrite=overwrite)