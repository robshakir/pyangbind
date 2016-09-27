"""
Copyright 2016, Google Inc.

Author: robjs@google.com

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

from pyang import util
from .misc import module_import_prefixes

class Identity(object):
  def __init__(self, name):
    self.name = name
    self.source_module = None
    self._imported_prefixes = []
    self.source_namespace = None
    self.base = None
    self.children = []

  def add_prefix(self, prefix):
    if not prefix in self._imported_prefixes:
      self._imported_prefixes.append(prefix)

  def add_child(self, child):
    if not isinstance(child, Identity):
      raise ValueError("Must supply a identity as a child")
    self.children.append(child)

  def __str__(self):
    return "%s:%s" % (self.source_module, self.name)

  def prefixes(self):
    return self._imported_prefixes

class IdentityStore(object):
  def __init__(self):
    self._store = []

  def find_identity_by_source_name(self, s, n):
    for i in self._store:
      if i.source_module == s and i.name == n:
        return i

  def add_identity(self, i):
    if isinstance(i, Identity):
      if not self.find_identity_by_source_name(i.source_module, i.name):
        self._store.append(i)
    else:
      raise ValueError("Must specify an identity")

  def identities(self):
    return ["%s:%s" % (i.source_module, i.name) for i in self._store]

  def __iter__(self):
    return iter(self._store) 

  def build_store_from_definitions(self, ctx, defnd):
    unresolved_identities = defnd.keys()
    unresolved_identity_count = {k: 0 for k in defnd}
    error_ids = []

    mod_ref_prefixes = module_import_prefixes(ctx)

    while len(unresolved_identities):
      this_id = unresolved_identities.pop(0)
      iddef = defnd[this_id]

      base = iddef.search_one('base')
      try:
        mainmod = iddef.main_module()
      except AttributeError:
        mainmod = None
      if mainmod is not None:
        defmod = mainmod

      defining_module = defmod.arg
      namespace = defmod.search_one('namespace').arg
      prefix = defmod.search_one('prefix').arg

      if base is None:
        # Add a new identity which can be a base
        tid = Identity(iddef.arg)
        tid.source_module = defining_module
        tid.source_namespace = namespace
        tid.add_prefix(prefix)
        self.add_identity(tid)

        if defining_module in mod_ref_prefixes:
          for i in mod_ref_prefixes[defining_module]:
            tid.add_prefix(i)

      else:
        # Determine what the name of the base and the prefix for
        # the base should be
        if ":" in base.arg:
          base_pfx, base_name = base.arg.split(":")
        else:
          base_pfx, base_name = prefix, base.arg

        parent_module = util.prefix_to_module(defmod, base_pfx, 
                                  base.pos, ctx.errors)

        # Find whether we have the base in the store
        base_id = self.find_identity_by_source_name(parent_module.arg, base_name)

        if base_id is None:
          # and if not, then push this identity back onto the stack
          unresolved_identities.append(this_id)
          unresolved_identity_count[this_id] += 1
          if unresolved_identity_count[this_id] > 1000:
            if unresolved_idc[ident] > 1000:
              sys.stderr.write("could not find a match for %s base: %s\n" %
                (iddef.arg, base_name))
              error_ids.append(ident)            
        else:
          # Check we don't already have this identity defined
          if self.find_identity_by_source_name(defining_module, iddef.arg) is None:
            # otherwise, create a new identity that reflects this one
            tid = Identity(iddef.arg)
            tid.source_module = defining_module
            tid.source_namespace = namespace
            tid.add_prefix(prefix)
            base_id.add_child(tid)
            self.add_identity(tid)

            if defining_module in mod_ref_prefixes:
              for i in mod_ref_prefixes[defining_module]:
                tid.add_prefix(i)

      if error_ids:
        raise TypeError("could not resolve identities %s" % error_ids)

    self._build_inheritance()

  def _recurse_children(self, identity, children):
    for child in identity.children:
      children.append(child)
      self._recurse_children(child, children)
    return children


  def _build_inheritance(self):
    for i in self._store:
      ch = list()
      self._recurse_children(i, ch)
      i.children = ch