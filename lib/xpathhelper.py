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
import uuid
import sys

class XPathError(Exception):
  pass

class YANGPathHelper(object):
  _attr_re = re.compile("^(?P<tagname>.*)\[(?P<arg>.*)\]$")
  _arg_re = re.compile("^[@]?(?P<cmd>[a-zA-Z0-9\-\_]+)([ ]+)?=([ ]+)?[\'\"]?(?P<arg>[^ ^\'^\"]+)([\'\"])?([ ]+)?(?P<remainder>.*)")
  _relative_path_re = re.compile("^(\.|\.\.)")

  def __init__(self):
    self._root = etree.Element("root")
    self._library = {}

  def _encode_path(self, path, mode="search", find_parent=False):
      if not mode in ["search", "set"]:
        raise XPathError, "Path can only be encoded based on searching or setting attributes"
      epath = ""
      parts = path.split("/")

      if find_parent and len(parts) == 2:
        return "/"

      lastelem = len(parts)-1 if find_parent else len(parts)
      for i in range(1,lastelem):
        (tagname, attributes) = self._tagname_attributes(parts[i])
        if attributes is not None:
          epath += "/" + tagname + "["
          #print "ATTRS WAS %s" % attributes
          for k,v in attributes.iteritems():
            epath += "@%s='%s' " % (k,v)
            if mode == "search":
              epath += "and "
          if mode == "search":
            epath = epath.rstrip("and ")
          epath = epath.rstrip(" ") + "]"
        else:
          epath += "/" + tagname
      return epath

  def _tagname_attributes(self, tag):
      tagname,attributes = tag,None
      if self._attr_re.match(tag):
        tagname,arg = self._attr_re.sub('\g<tagname>||\g<arg>', tag).split("||")
        attributes = {}
        cmd_arg_pairs = []
        tmp_arg = arg
        while len(tmp_arg):
          if self._arg_re.match(tmp_arg):
            c,a,r = self._arg_re.sub('\g<cmd>||\g<arg>||\g<remainder>', tmp_arg).split("||")
            attributes[c] = a
            tmp_arg = r
          else:
            raise XPathError, "invalid attribute string specified for %s - %s" % (tagname, arg)
      return (tagname, attributes)

  def register(self, object_path, ptr, caller=False):
    #print "REGISTERING %s" % object_path
    #print self.tostring(pretty_print=True)
    if not re.match("^(\.|\.\.|\/)", object_path):
      raise XPathError("A valid relative or absolute path must start with '.', '..', or '/'")

    # check whether we're updating
    this_obj_existing = self._get_etree(object_path)
    if len(this_obj_existing) > 1:
      raise XPathError, "duplicate objects in tree - %s" % object_path
    if this_obj_existing is not None and not this_obj_existing == []:
      this_obj_existing = this_obj_existing[0]
      if self._library[this_obj_existing.get("obj_ptr")] == ptr:
        return True
      else:
        del self._library[this_obj_existing.get("obj_ptr")]
        new_uuid = str(uuid.uuid1())
        self._library[new_uuid] = ptr
        this_obj_existing.set("obj_ptr", new_uuid)
        return True

    this_obj_id = str(uuid.uuid1())
    self._library[this_obj_id] = ptr
    parent = self._encode_path(object_path, mode="set", find_parent=True)
    pparts = object_path.split("/")
    (tagname, attributes) = self._tagname_attributes(pparts[len(pparts)-1])

    #print "CHECKING @ %s" % parent
    if parent == "/":
      parent_o = self._root
    else:
      parent_o = self._get_etree(parent)
      if len(parent_o) > 1:
        raise XPathError, "multiple elements returned for parent %s, must be exact path for registration" \
          % parent
      if parent_o == []:
        raise XPathError, "parent node did not exist for %s @ %s" % (tagname, parent)
      parent_o = parent_o[0]

    #sys.stderr.write("registering %s @ %s - %s w/ %s\n" % (tagname, parent, parent_o, attributes))
    added_item = etree.SubElement(parent_o, tagname, obj_ptr=this_obj_id)
    if attributes is not None:
      for k,v in attributes.iteritems():
        added_item.set(k,v)

  def _get_etree(self, object_path, caller=False):
    fx_q = self._encode_path(object_path)
    print "caller: %s: %s -> match(%s)" % (object_path, caller, self._relative_path_re.match(object_path))
    if self._relative_path_re.match(object_path) and caller:
      fx_q = "." + caller + "/" + object_path
      print "caller@_get_etree: fx_q: %s" % fx_q
    else:
      fx_q = "."+fx_q
    print "caller: fx_q is %s" % fx_q
    retr_obj = self._root.xpath(fx_q)
    print "caller: retr %s" % retr_obj
    return retr_obj

  def get(self, object_path, caller=False):
    print "caller@get: %s" % caller
    return [self._library[i.get("obj_ptr")] for i in self._get_etree(object_path, caller=caller)]


  def tostring(self,pretty_print=False):
    return etree.tostring(self._root,pretty_print=pretty_print)