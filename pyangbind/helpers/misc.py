"""
Copyright 2015, Rob Shakir 
Modifications copyright 2016, Google Inc.

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

def module_import_prefixes(ctx):
  mod_ref_prefixes = {}
  for mod in ctx.modules:
    m = ctx.search_module(0, mod[0])
    for importstmt in m.search('import'):
      if not importstmt.arg in mod_ref_prefixes:
        mod_ref_prefixes[importstmt.arg] = []
      mod_ref_prefixes[importstmt.arg].append(importstmt.search_one('prefix').arg)
  return mod_ref_prefixes

def find_child_definitions(obj, defn, prefix, definitions):
  for i in obj.search(defn):
    if i.arg in definitions:
      sys.stderr.write("WARNING: duplicate definition of %s" % i.arg)
    else:
      definitions["%s:%s" % (prefix, i.arg)] = i

  for ch in obj.search('grouping'):
    if ch.i_children:
      find_child_definitions(ch, defn, prefix, definitions)

  return definitions


def find_definitions(defn, ctx, module, prefix):
  # Find the statements within a module that map to a particular type of
  # statement, for instance - find typedefs, or identities, and reutrn them
  # as a dictionary to the calling function.
  definitions = {}
  defin = find_child_definitions(module, defn, prefix, definitions)
  return defin