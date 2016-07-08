"""
Copyright 2015, Rob Shakir (rjs@jive.com, rjs@rob.sh)

This project has been supported by:
          * Jive Communcations, Inc.
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


class PybindBase(object):

  __slots__ = ()

  def elements(self):
    return self._pyangbind_elements

  def __str__(self):
    return str(self.elements())

  def get(self, filter=False):
    def error():
      return NameError, "element does not exist"

    d = {}
    # for each YANG element within this container.
    for element_name in self._pyangbind_elements:
      element = getattr(self, element_name, error)
      if hasattr(element, "yang_name"):
        # retrieve the YANG name method
        yang_name = getattr(element, "yang_name", error)
        element_id = yang_name()
      else:
        element_id = element_name

      if hasattr(element, "get"):
        # this is a YANG container that has its own
        # get method
        d[element_id] = element.get(filter=filter)
        if filter is True:
          # if the element hadn't changed but we were
          # filtering unchanged elements, remove it
          # from the dictionary
          if isinstance(d[element_id], dict):
            for entry in d[element_id].keys():
              changed, present = False, False

              if hasattr(d[element_id][entry], "_changed"):
                if d[element_id][entry]._changed():
                  changed = True
              else:
                changed = None

              if hasattr(d[element_id][entry], "_present"):
                if not d[element_id][entry]._present() is True:
                  present = True
              else:
                present = None

              if present is False and changed is False:
                del d[element_id][entry]

            if len(d[element_id]) == 0:
              if element._presence and element._present():
                pass
              else:
                del d[element_id]
          elif isinstance(d[element_id], list):
            for list_entry in d[element_id]:
              if hasattr(list_entry, "_changed"):
                if not list_entry._changed():
                  d[element_id].remove(list_entry)
            if len(d[element_id]) == 0:
              del d[element_id]
      else:
        # this is an attribute that does not have get()
        # method
        if filter is False and not element._changed() and not element._present() is True:
          if element._default is not False and element._default:
            d[element_id] = element._default
          else:
            d[element_id] = element
        elif element._changed() or element._present() is True:
          d[element_id] = element
        else:
          # changed = False, and filter = True
          pass
    return d

  def __getitem__(self, k):
    def error():
      raise KeyError("Key %s does not exist" % k)
    element = getattr(self, k, error)
    return element()

  def __iter__(self):
    for elem in self._pyangbind_elements:
      yield (elem, getattr(self, elem))
