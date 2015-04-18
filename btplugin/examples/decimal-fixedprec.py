

from decimal import Decimal

def RestrictedPrecisionDecimalType(*args, **kwargs):
	print "asked to pop"
	precision = False
	precision = kwargs.pop("precision", False)
	print precision
	print precision
	class RestrictedPrecisionDecimal(Decimal):
		_precision = 10.0**(-1.0*int(precision))
		def __new__(self, *args, **kwargs):
			if not self._precision == None:
				if len(args):
					value = Decimal(args[0]).quantize(Decimal(str(self._precision)))
				else:
					value = Decimal(0)
			elif len(args):
				value = Decimal(args[0])
			else:
				value = Decimal(0)
			obj = Decimal.__new__(self, value, **kwargs)
			return obj

		#def __init__(self, *args, **kwargs):
		#	super(RestrictedPrecisionDecimal, self).__init__(*args, **kwargs)


	return type(RestrictedPrecisionDecimal(*args, **kwargs))

f = RestrictedPrecisionDecimalType(precision=4)
g = f(2.4009)
print g

x = RestrictedPrecisionDecimalType(precision=3)
y = x(2.4009)
print y
