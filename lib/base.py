import copy

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
        if filter == True:
          # if the element hadn't changed but we were
          # filtering unchanged elements, remove it
          # from the dictionary
          if isinstance(d[element_id], dict):
            for entry in d[element_id]:
              if hasattr(d[element_id][entry], "_changed"):
                if not d[element_id][entry]._changed():
                  del d[element_id][entry]
            if len(d[element_id]) == 0:
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
        if filter == False and not element._changed():
          if not element._default == False and element._default:
            d[element_id] = element._default
          else:
            d[element_id] = element
        elif element._changed():
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
