from bindings import ptr_tc02 as ytest
from xpathhelper import YANGPathHelper
yhelper =  YANGPathHelper()
yobj = ytest(path_helper=yhelper)

yobj.container.t1a.add("test")

import pprint

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(yobj.get())

yobj.container.t1a["test"].t1c.t1d = 'fish'
pp.pprint(yobj.get())