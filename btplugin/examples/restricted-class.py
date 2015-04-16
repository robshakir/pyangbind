
import re

def RestrictedClassType(*args, **kwargs):
  base_type = kwargs.pop("base_type", str)
  restriction_type = kwargs.pop("restriction_type", None)
  restriction_arg = kwargs.pop("restriction_arg", None)

  class RestrictedClass(base_type):
    _restriction_type = restriction_type
    _restriction_arg = restriction_arg
    _restriction_test = None

    def __init__(self, *args, **kwargs):
      if self._restriction_type == "pattern":
        p = re.compile(self._restriction_arg)
        self._restriction_test = p.match
      super(RestrictedClass, self).__init__(*args, **kwargs)

    def __new__(self, *args, **kwargs):
      obj = base_type.__new__(self, *args, **kwargs)
      return obj

    def __check(self, v):
      if self._restriction_type == "pattern":
        if not self._restriction_test.match(v):
          return False
        return True

    def __setitem__(self, *args, **kwargs):
      print "Called"
      if not self.__check(args[0]):
        return ValueError, "did not match restricted type"
      super(RestrictedClass, self).__setitem__(*args, **kwargs)

  return type(RestrictedClass(*args, **kwargs))


t = RestrictedClassType("aardvark", base_type=str, restriction_type="pattern", restriction_arg="^a")
print type(t)
print t
t="fish"
print type(t)