import collections

def defineTypedListClass(*args,**kwargs):
  class TypedList(collections.MutableSequence):
    def __init__(self, *args, **kwargs):
      self.allowed_types = kwargs.pop("allowed_types", str)
      self.list = list()
      self.extend(list(args))

    def check(self, v):
      if not isinstance(v, self.allowed_types):
        raise TypeError, v

    def __len__(self): return len(self.list)

    def __getitem__(self,i): return self.list[i]

    def __delitem__(self,i): del self.list[i]

    def __setitem__(self, i, v):
      self.check(v)
      self.list[i] = v

    def insert(self, i, v):
      self.check(v)
      self.list.insert(i,v)

    def __str__(self):
      return str(self.list)
  return TypedList(*args,**kwargs)


t = defineTypedListClass(allowed_types=str)

print type(t)
t.append("fish")
t.append("1")
try:
    t.append(int(1))
except:
    print "success"
    pass
print t

