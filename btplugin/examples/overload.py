
import numpy as np
import collections
import sys

#def yang_set(self):
#   return self._changed

def TypedListType(*args, **kwargs):
  allowed_type = kwargs.pop("allowed_type", str)
  # this was from collections.MutableSequence
  class TypedList(collections.MutableSequence):
    _list = list()
    _allowed_type = allowed_type

    def __init__(self, *args, **kwargs):
      self._list.extend(list(args))

    def check(self,v):
      if not isinstance(v, self._allowed_type):
        raise TypeError("Cannot add %s to TypedList (accepts only %s)" % (v, self._allowed_type))

    def __len__(self): return len(self._list)
    def __getitem__(self,i): return self._list[i]
    def __delitem__(self): del self._list[i]
    def __setitem__(self, i, v):
      self.check(v)
      self._list.insert(i,v)

    def insert(self, i, v):
      self.check(v)
      self._list.insert(i,v)

    def __str__(self):
      return str(self._list)
  return type(TypedList(*args,**kwargs))

class YANGBool(int):
  __v = 0
  def __init__(self,v=False):
    if v in [0, False, "false", "False"]:
      self.__v = 0
    else:
      self.__v = 1
  def __repr__(self):
    return str(True if self.__v else False)

def defineYANGDynClass(*args, **kwargs):
  base_type = kwargs.pop("base",int)
  class YANGDynClass(base_type):
    _changed = False
    _default = False

    def yang_set(self):
      return self._changed

    def __setitem__(self, *args, **kwargs):
      self._changed = True
      super(YANGDynClass, self).__setitem__(key, value)

    def append(self, *args, **kwargs):
      if not hasattr(super(YANGDynClass,self), "append"):
        raise AttributeError("%s object has no attribute append" % base_type)
      self._changed = True
      super(YANGDynClass, self).append(*args,**kwargs)

    def pop(self, *args, **kwargs):
      if not hasattr(super(YANGDynClass, self), "pop"):
        raise AttributeError("%s object has no attribute pop" % base_type)
      self._changed = True
      super(YANGDynClass, self).pop(*args, **kwargs)

    def remove(self, *args, **kwargs):
      if not hasattr(super(YANGDynClass, self), "remove"):
        raise AttributeError("%s object has no attribute remove" % base_type)
      self._changed = True
      super(YANGDynClass, self).remove(*args, **kwargs)

    def extend(self, *args, **kwargs):
      if not hasattr(super(YANGDynClass, self), "extend"):
        raise AttributeError("%s object has no attribute extend" % base_type)
      self._changed = True
      super(YANGDynClass, self).extend(*args, **kwargs)

    def insert(self, *args, **kwargs):
      if not hasattr(super(YANGDynClass,self), "insert"):
        raise AttributeError("%s object has no attribute insert" % base_type)
      self._changed = True
      super(YANGDynClass, self).insert(*args, **kwargs)

    def __repr__(self, *args, **kwargs):
      if self._default and not self._changed:
        return repr(self._default)
      else:
        return super(YANDDynClass, self).__repr__()

    def __init__(self, *args, **kwargs):
      pass

    def __new__(self, *args, **kwargs):
      default = kwargs.pop("default", None)
      try:
        value = args[0]
      except IndexError:
        value = None

      obj = base_type.__new__(self, *args, **kwargs)
      if default == None:
        if value == None or value == base_type():
          # there was no default, and the value was not set, or was
          # set to the default of the base type
          obj._changed = False
        else:
          # there was no default, and the value was something other
          # than a default - the object has changed
          obj._changed = True
      else:
        # there is a default - if the value is not the same as that default
        # then we have changed the object.
        if value == None:
          # if the value is none, then we have not changed it
          obj._changed = False
        elif not value == default:
          obj._changed = True
        else:
          obj._changed = False

      obj._default = default
      return obj

  return YANGDynClass(*args,**kwargs)


t = defineYANGDynClass(base=TypedListType(allowed_type=str))
c = defineYANGDynClass(1,default=1,base=int)
d = defineYANGDynClass(2,base=int)
e = defineYANGDynClass(3,base=np.uint8,default=10)
f = defineYANGDynClass("hello",base=str)
g = defineYANGDynClass(default=["hello",],base=list)
#print type(e)
h = defineYANGDynClass(True, base=YANGBool)
i = defineYANGDynClass(default="fish", base=str)
#print type(h)

#print len(g)
#g.append("fish")
#print len(g)

print type(f)
print f
if f == "hello":
  print "this worked"
else:
  print "this did not work"

#q = defineTypedListClass(base=str)
#t = defineYANGDynClass(base=type(defineTypedListClass(allowed_types=str)))
#t = defineYANGDynClass(base=type(TypedList(allowed_type=str)))
#t.append("fish")
#try:
#  t.append(int(1))
#except TypeError:
#  print "Expected"
#  pass
#print t
#print len(t)
#print t[::2]
q = defineYANGDynClass(base=TypedListType(allowed_type=int))
print "%s,%s" % (q,q.yang_set())
q.extend([1,2,3])
print "%s,%s" % (q, q.yang_set())
print "%s,%s" % (t,t.yang_set())
t.append("hello")
print "%s,%s" % (t, t.yang_set())

try:
  c.append(1)
except AttributeError:
  print "Expected"
#t.append("hello")
#print g
#print i
#print i.yang_set()
#print g
print "c: %d, d: %d, e: %d, f: %s, g: %s, h: %s, i: %s, t: %s" % (c,d,e, f, g, h, i, t)
print "c: %s, d: %s, e: %s, f: %s, g: %s, h: %s, i: %s, t: %s" % (c.yang_set(), d.yang_set(), e.yang_set(), f.yang_set(), g.yang_set(), h.yang_set(), i.yang_set(), t.yang_set())

print "c (%s - %s) + d (%s - %s) -> %d + %d = %d" % (c, c.yang_set(),d, d.yang_set(),c,d,c+d)
c=c+d
#print "c now %s, %s" % (c, c.yang_set())

#print c.yang_set()
#print d.yang_set()
#print e.yang_set()

#print (c+d)
#print (d+e)

#t = defineYANGDynClass(base=TypedList)

#strTypeList = type('StrTypedList', (type(TypedList(str)),), {})

#t = defineYANGDynClass(base=type('StrTypedList', (type(TypedList(str)),), {}))

#t.append("fish")
#t.append(int(1))

#c = YANGInt(1, default=1)
#d = YANGInt(2)
#e = YANGInt()

#print c.yang_set()
#print d.yang_set()
#print e.yang_set()

#print (c+d)
#print (d+e)


    # class YANGInt(int):
    #   _changed = False

    #   def yang_set(self):
    #       return self._changed

    #   def __new__(self, *args, **kwargs):
    #       default = kwargs.pop("default", None)
    #       try:
    #           value = args[1]
    #       except IndexError:
    #           value = None

    #       obj = int.__new__(self, *args, **kwargs)
    #       obj._changed = True if (default == None and not value == None) \
    #                           or (not default == None and not value == default) \
    #                           else False
    #       return obj