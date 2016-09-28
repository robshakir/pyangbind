"""
Copyright 2015, Rob Shakir (rjs@jive.com, rjs@rob.sh)

Modifications copyright 2016, Google Inc.

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

xpathhelper:
  This module maintains an XML ElementTree for the registered Python
  classes, so that XPATH can be used to lookup particular items.
"""

from lxml import etree
import re
import uuid
import sys
from .yangtypes import safe_name
from .base import PybindBase


class YANGPathHelperException(Exception):
  pass


class XPathError(Exception):
  pass


class PybindImplementationError(Exception):
  pass


class PybindXpathHelper(object):
  def register(self, path, object_ptr, caller=False):
    """
      A PybindXpathHelper class should supply a register() method that
      takes two mandatory arguments, and one optional.

      * path - the path to which the object should be registered. This is
        supplied as a list of the names of the elements of the path. For
        example, /device/interfaces/interface[name='eth0'] is supplied as
        a ["device", "interfaces", "interface[@name='eth0']"].

      * object_ptr - a reference to the object that is to be stored at this
        location in the tree.

      * caller=False - this supplies the path of the object that is currently
        trying to perform a register. In general, it will not be used, but it
        is supplied to facilitate relative path lookups.
    """
    raise PybindImplementationError("The path helper class specified does " +
                                    "not implement register()")

  def unregister(self, path, caller=False):
    """
      A PybindXpathHelper class should supply an unregister() method that
      takes one mandatory argument, and one optional.

      * path - the path of the object to be unregistered. Supplied as a list()
        object of the elements of the path.

      * caller=False - the absolute path of the object calling the unregister()
        method.
    """
    raise PybindImplementationError("The path helper class specified does " +
                                    "not implement unregister()")

  def get(self, path, caller=False):
    """
      A PybindXpathHelper class should supply a get() method that takes one
      mandatory argument and one optional.

      * path - the path to the object to be retrieved. This may be specified as
        a list of parts, or an XPATH expression.

      * caller=False - the absolute path of the object calling the get method.
    """
    raise PybindImplementationError("The path helper class specified does " +
                                    "not implement get()")


# A class which acts as "/" within the hierarchy - it acts as per any other
# PyangBind element for the purposes of get() calls - allowing "/" to be
# serialised to
class FakeRoot(PybindBase):
  def __init__(self):
    self._pyangbind_elements = {}

class YANGPathHelper(PybindXpathHelper):
  _attr_re = re.compile("^(?P<tagname>[^\[]+)(?P<args>(\[[^\]]+\])+)$")
  _arg_re = re.compile("^((and|or) )?[@]?(?P<cmd>[a-zA-Z0-9\-\_:]+)([ ]+)?" +
                       "=([ ]+)?[\'\"]?(?P<arg>[^ ^\'^\"]+)([\'\"])?([ ]+)?" +
                       "(?P<remainder>.*)")
  _relative_path_re = re.compile("^(\.|\.\.)")

  def __init__(self):
    # Initialise an empty library and a new FakeRoot class to act as the
    # data tree's root.
    self._root = etree.Element("root")
    self._library = {}
    self._library["root"] = FakeRoot()
    self._root.set("obj_ptr", "root")

  def _path_parts(self, path):
    c = 0
    parts = []
    buf = ""
    in_qstr, in_attr = False, False
    while c < len(path):
      if path[c] == "/" and not in_qstr and not in_attr:
        parts.append(buf)
        buf = ""
      elif path[c] == '"' and in_qstr:
        in_qstr = False
        buf += path[c]
      elif path[c] == '"':
        in_qstr = True
        buf += path[c]
      elif path[c] == '[':
        in_attr = True
        buf += path[c]
      elif path[c] == ']':
        in_attr = False
        buf += path[c]
      else:
        buf += path[c]
      c += 1
    parts.append(buf)
    return parts

  def _encode_path(self, path, mode="search", find_parent=False,
                   normalise_namespace=True, caller=False):
    if mode not in ["search", "set"]:
      raise XPathError("Path can only be encoded based on searching or " +
                       "setting attributes")

    parts = path
    if len(parts) == 0:
      return "/"
    elif find_parent and len(parts) == 1:
      return []

    lastelem = len(parts) - 1 if find_parent else len(parts)
    startelem = 1 if parts[0] == '' else 0
    if self._relative_path_re.match(parts[0]):
      epath = ""
    else:
      epath = "/"
    for i in range(startelem, lastelem):
      (tagname, attributes) = self._tagname_attributes(parts[i],
                                    normalise_namespace=normalise_namespace)
      if ":" in tagname and normalise_namespace:
        tagname = tagname.split(":")[1]

      if attributes is not None:
        epath += tagname + "["
        for k, v in attributes.iteritems():
          # handling for rfc6020 current() specification
          if "current()" in v:
            remaining_path = re.sub("current\(\)(?P<remaining>.*)",
                                      '\g<remaining>', v).split("/")
            # since the calling leaf may not exist, we need to do a
            # lookup on a path that will do, which is the parent
            if remaining_path[1] == "..":
              lookup = caller[:-1] + remaining_path[2:]
            else:
              lookup = caller + remaining_path[1:]
            resolved_current_attr = self.get(lookup)
            if not len(resolved_current_attr) == 1:
              raise XPathError('XPATH specified a current() expression that ' +
                                'returned a non-unique list')
            v = resolved_current_attr[0]
          epath += "@%s='%s' " % (k, v)
          if mode == "search":
            epath += "and "
        if mode == "search":
          epath = epath.rstrip("and ")
        epath = epath.rstrip(" ") + "]"
        epath += "/"
      else:
        epath += tagname + "/"
    epath = epath.rstrip("/")
    return epath

  def _tagname_attributes(self, tag, normalise_namespace=True):
    tagname, attributes = tag, None
    if self._attr_re.match(tag):
      tagname, args = self._attr_re.sub('\g<tagname>||\g<args>',
                                        tag).split("||")
      arg_parts = [i.strip("[") for i in args.split("]")]

      attributes = {}
      for arg in arg_parts:
        tmp_arg = arg
        while len(tmp_arg):
          if self._arg_re.match(tmp_arg):
            c, a, r = self._arg_re.sub('\g<cmd>||\g<arg>||\g<remainder>',
                                        tmp_arg).split("||")
            if ":" in c and normalise_namespace:
              c = c.split(":")[1]
            attributes[c] = a
            tmp_arg = r
          else:
            raise XPathError("invalid attribute string specified" +
                             "for %s" % tagname +
                             "(err part: %s (%s))" % (arg, tmp_arg))
    return (tagname, attributes)

  def register(self, object_path, object_ptr, caller=False):
    if isinstance(object_path, str):
      raise XPathError("not meant to receive strings as input to register()")

    if re.match('^\.\.', object_path[0]):
      raise XPathError("unhandled relative path in register()")

    # This is a hack to register anything that is a top-level object,
    # it allows modules to register themselves against the FakeRoot
    # class which acts as per other PyangBind objects.
    if len(object_path) == 1:
      setattr(self._library["root"], object_path[0], object_ptr)
      setattr(self._library["root"], "_get_%s" % safe_name(object_path[0]), lambda: object_ptr)
      self._library["root"]._pyangbind_elements[object_path[0]] = None

    # check whether we're updating
    this_obj_existing = self._get_etree(object_path)
    if len(this_obj_existing) > 1:
      raise XPathError("duplicate objects in tree - %s" % object_path)
    if this_obj_existing is not None and not this_obj_existing == []:
      this_obj_existing = this_obj_existing[0]
      if self._library[this_obj_existing.get("obj_ptr")] == object_ptr:
        return True
      else:
        del self._library[this_obj_existing.get("obj_ptr")]
        new_uuid = str(uuid.uuid1())
        self._library[new_uuid] = object_ptr
        this_obj_existing.set("obj_ptr", new_uuid)
        return True

    this_obj_id = str(uuid.uuid1())
    self._library[this_obj_id] = object_ptr
    parent = object_path[:-1]
    (tagname, attributes) = self._tagname_attributes(object_path[-1])

    if parent == []:
      parent_o = self._root
    else:
      parent_o = self._get_etree(parent)
      if len(parent_o) > 1:
        raise XPathError("multiple elements returned for parent %s, must be " +
                          "exact path for registration" % "/" +
                          "/".join(parent))
      if parent_o == []:
        raise XPathError("parent node did not exist for %s @ %s" % (tagname,
                                    "/" + "/".join(parent)))
      parent_o = parent_o[0]

    added_item = etree.SubElement(parent_o, tagname, obj_ptr=this_obj_id)
    if attributes is not None:
      for k, v in attributes.iteritems():
        added_item.set(k, v)

  def unregister(self, object_path, caller=False):
    if isinstance(object_path, str):
      raise XPathError("should not receive paths as a str in unregister()")
    if re.match("^(\.|\.\.|\/)", object_path[0]):
      raise XPathError("unhandled relative path in unregister()")

    existing_objs = self._get_etree(object_path)
    if len(existing_objs) == 0:
      raise XPathError("object did not exist to unregister - %s" % object_path)

    for obj in existing_objs:
      ref = obj.get("obj_ptr")
      del self._library[ref]
      obj.getparent().remove(obj)

  def _get_etree(self, object_path, caller=False):
    fx_q = self._encode_path(object_path, caller=caller)
    if self._relative_path_re.match(fx_q) and caller:
      fx_q = "." + self._encode_path(caller)
      fx_q += "/" + self._encode_path(object_path, caller=caller)
    else:
      if not fx_q == "/":
        fx_q = "." + fx_q

    retr_obj = self._root.xpath(fx_q)
    return retr_obj

  def get(self, object_path, caller=False):
    if isinstance(object_path, str) or isinstance(object_path, unicode):
      object_path = self._path_parts(object_path)

    return [self._library[i.get("obj_ptr")]
              for i in self._get_etree(object_path, caller=caller)]

  def get_unique(self, object_path, caller=False,
                  exception_to_raise=YANGPathHelperException):
    obj = self.get(object_path, caller=caller)
    if len(obj) == 0:
      raise exception_to_raise("Supplied path for %s found no results!"
                                  % object_path)
    if len(obj) != 1:
      raise exception_to_raise("Supplied path for %s was not unique!"
                                  % object_path)
    return obj[0]

  def get_list(self, object_path, caller=False,
                exception_to_raise=YANGPathHelperException):
    if isinstance(object_path, str) or isinstance(object_path, unicode):
      object_path = self._path_parts(object_path)

    parent_obj = self.get_unique(object_path[:-1], caller=caller,
                    exception_to_raise=exception_to_raise)

    list_get_attr = getattr(parent_obj, "_get_%s" % safe_name(object_path[-1]), None)
    if list_get_attr is None:
      raise exception_to_raise("Element %s does not have an attribute named %s" % ("/".join(object_path[:-1]), object_path[-1]))

    return list_get_attr()

  def tostring(self, pretty_print=False):
    return etree.tostring(self._root, pretty_print=pretty_print)
