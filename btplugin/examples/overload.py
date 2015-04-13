
import numpy as np

#def yang_set(self):
#   return self._changed

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

    def __repr__(self):
      #print self._default
      ####
      #
      # if a variable is not set in YANG, then if we print it, it should
      # still show the default value.
      # but, when doing a comparison, then it should not be equal (it should)
      # rather be equal to the unset value
      #
      ###
      if self._default and not self._changed:
        return repr(self._default)
      else:
        return super(YANGDynClass, self).__repr__()

    def __str__(self):
      return self.__repr__()

    def __init__(self, *args, **kwargs):
      #print "__init__ was called with %s and %s" % (args, kwargs)
      pass

    def __new__(self, *args, **kwargs):
      #print "__new__ was called with %s and %s" % (args, kwargs)
      default = kwargs.pop("default", None)
      try:
        value = args[0]
      except IndexError:
        value = None

      #print "args: %s, kwargs: %s" % (args,kwargs)
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

c = defineYANGDynClass(1,default=1,base=int)
d = defineYANGDynClass(2,base=int)
e = defineYANGDynClass(3,base=np.uint8,default=10)
f = defineYANGDynClass("hello",base=str)
g = defineYANGDynClass(default=["hello",],base=list)
#print type(e)
h = defineYANGDynClass(True, base=YANGBool)
i = defineYANGDynClass(default="fish", base=str)
#print type(h)

#print g
#print i
print i.yang_set()
#print g
print "c: %d, d: %d, e: %d, f: %s, g: %s, h: %s, i: %s" % (c,d,e, f, g, h, i)
print "c: %s, d: %s, e: %s, f: %s, g: %s, h: %s, i: %s" % (c.yang_set(), d.yang_set(), e.yang_set(), f.yang_set(), g.yang_set(), h.yang_set(), i.yang_set())

#print c.yang_set()
#print d.yang_set()
#print e.yang_set()

#print (c+d)
#print (d+e)



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