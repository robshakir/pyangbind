import inspect

def partialmethod(method, *args, **kw):
  def call(obj, *more_args, **more_kw):
    call_kw = kw.copy()
    call_kw.update(more_kw)
    print method
    return getattr(obj, method)(*(args+more_args), **call_kw)
  return call

def borrow_methods(source_type, overwrite=False, exclude=None, include=None,
    uncasted=None):
    '''
    Decorator for borrowing methods from other classes.
    Note: 'include' has priority over 'exclude'.
    '''
    if not exclude:
        exclude = ['__getnewargs__']
    if not include:
        include = ['__repr__', '__format__', '__str__']
    if not uncasted:
        uncasted = ['__int__', '__str__', '__cmp__'] # removed __cmp__

    #uncasted = [name for name in dir(source_type)]

    def invoke_method(self, method_name, *args, **keywords):
        #prior_value = getattr(self.value)
        prev_value = self.value
        method = getattr(self.value, method_name)
        print "called"
        result = method(*args, **keywords)
        if not result == prev_value:
          self._is_set = True
        if method_name not in uncasted and type(self) != type(result):
            result = self.__class__(result)
            print method_name
        return result

    def decorator(cls):
        setattr(cls, '_is_set', False)
        setattr(cls, '_invoke_method', invoke_method)
        for (name, member) in inspect.getmembers(source_type):
            if (not overwrite and hasattr(cls, name)) \
                or (name in exclude and not name in include) \
                or not inspect.ismethoddescriptor(member):
                continue
            setattr(cls, name, partialmethod('_invoke_method', name))
        return cls
    return decorator

class YANGBase(object):
  def __init__(self, value):
    self.value = value

@borrow_methods(int)
class YANGInt(YANGBase):
  pass


i = YANGInt(1)
j = YANGInt(2)
print dir(j)
print j.__str__()
print (i+j)
#print (i == j)
#print (i+j)
#print (j-i)
