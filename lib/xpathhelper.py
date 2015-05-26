"""
Copyright 2015  Rob Shakir, BT plc. (rob.shakir@bt.com, rjs@rob.sh)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

xpathhelper:
	This module maintains an XML ElementTree for the registered Python
	classes, so that XPATH can be used to lookup particular items.
"""

from lxml import etree
import re

class XPathError(Exception):
  pass

class YANGPathHelper(object):
  _attr_re = re.compile("(?P<tagname>.*)\[(?P<attr>.*)[ ]?=[ ]?(?P<val>.*)\]")
  _numeric_re = re.compile("^[0-9]+$")
  _numeric_fix_re = re.compile("^(?P<added>i\_\_)(?P<numeric>[0-9]+)$")

  def __init__(self):
    self._root = etree.Element("root")
    self._library = {}

  def _fix_query_string(self, path):
    parts = path.split("/")
    path = ""
    for path_p in parts:
      # if "[" in path_p:
      #   path_p = re.sub("\[", "[@", path_p)
      if self._attr_re.match(path_p):
        tagname,key,val = self._attr_re.sub("\g<tagname>,\g<attr>,\g<val>", path_p).split(",")
        if not re.match("^[\'\"].*[\'\"]$", val):
          val = "'%s'" % val
        path_p = "%s[@%s=%s]" % (tagname, key, val)
      if self._numeric_re.match(path_p):
        path_p = "i__%s" % path_p
      elif self._numeric_fix_re.match(path_p):
        path_p = self._numeric_fix_re.sub('\g<numeric>',path_p)
      path += path_p + "/"
    path = path.rstrip("/")
    return path

  def register(self, object_path, ptr, caller=False):
    if object_path == "root":
      return True
    if not re.match("^(\.|\.\.|\/)", object_path):
      raise XPathError("A valid relative or absolute path must start with '.', '..', or '/'")
    fx_object_path = self._fix_query_string(object_path)
    path_parts = fx_object_path.split("/")
    if not len(path_parts)-2:
      parent = self._root
    else:
      pp = "."
      for i in range(1,len(path_parts)-1):
        pp += "/%s" % path_parts[i]
      parent = self._root.find(pp)
    self._library[object_path] = ptr

    elemname = path_parts[len(path_parts)-1]
    setk = False
    if "[" in elemname:
      tagname,key,val = self._attr_re.sub("\g<tagname>,\g<attr>,\g<val>", elemname).split(",")
      val = re.sub("[\'\"]", "", val)
      key = re.sub("^@", "", key)
      elemname = tagname
      setk = True
    print "REGISTERING AT %s/%s" % (parent, elemname)
    added_item = etree.SubElement(parent, elemname, obj=object_path)
    if setk:
      added_item.set(key, val)

  def get(self, object_path, caller=False):
    fx_q = self._fix_query_string(object_path)
    if not caller:
      fx_q = "."+fx_q
    retr_obj = self._root.find(fx_q)
    if retr_obj is None:
      raise KeyError, "object specified (%s) does not exist in tree" % object_path
    return self._library[retr_obj.get("obj")]

  def tostring(self,pretty_print=False):
    return etree.tostring(self._root,pretty_print=pretty_print)

