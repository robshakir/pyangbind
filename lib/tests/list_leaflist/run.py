#!/usr/bin/env python

import sys
import os

def main():
    pass

if __name__ == '__main__':
  import_path = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../..")
  sys.path.insert(0, import_path)
  from xpathhelper import YANGPathHelper, XPathError
  main()
