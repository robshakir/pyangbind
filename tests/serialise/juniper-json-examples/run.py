#!/usr/bin/env python

import os
import sys
import getopt
import json

from pyangbind.lib.xpathhelper import YANGPathHelper
from pyangbind.lib.serialise import pybindJSONDecoder

TESTNAME = "json-serialise"


# generate bindings in this folder
def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "k", ["keepfiles"])
  except getopt.GetoptError as e:
    print str(e)
    sys.exit(127)

  k = False
  for o, a in opts:
    if o in ["-k", "--keepfiles"]:
      k = True

  pythonpath = os.environ.get("PATH_TO_PYBIND_TEST_PYTHON") if \
                os.environ.get('PATH_TO_PYBIND_TEST_PYTHON') is not None \
                  else sys.executable
  pyangpath = os.environ.get('PYANGPATH') if \
                os.environ.get('PYANGPATH') is not None else False
  pyangbindpath = os.environ.get('PYANGBINDPATH') if \
                os.environ.get('PYANGBINDPATH') is not None else False
  assert pyangpath is not False, "could not find path to pyang"
  assert pyangbindpath is not False, "could not resolve pyangbind directory"

  this_dir = os.path.dirname(os.path.realpath(__file__))
  files_str = " ".join([os.path.join(this_dir, "openconfig-bgp", i) for i in os.listdir(os.path.join(this_dir, "openconfig-bgp"))])

  cmd = "%s "% pythonpath
  cmd += "%s --plugindir %s/pyangbind/plugin" % (pyangpath, pyangbindpath)
  cmd += " -f pybind --split-class-dir %s/ocbind" % this_dir
  cmd += " -p %s" % this_dir
  cmd += " -p %s" % os.path.join(this_dir, "include")
  cmd += files_str
  # NB: use-xpathhelper is NOT specified here, so we don't try and do anything with leafrefs
  os.system(cmd)

  import ocbind

  yh = YANGPathHelper()

  json_dir = os.path.join(this_dir, "json")

  jbgp_global_ex = json.load(open(os.path.join(json_dir, "bgp-global-ex.json"), 'r'))
  ljs = pybindJSONDecoder.load_ietf_json(jbgp_global_ex["configuration"], ocbind, "openconfig_bgp", path_helper=yh)
  expected_ljs = \
    {
      "bgp" : {
        "global" : {
           "confederation" : {
              "config" : {
                 "identifier" : 65517,
                 "enabled" : True,
                 "member-as" : [
                    65518,
                    65519,
                    65520
                 ]
              }
           }
        }
      }
    }
  assert ljs.get(filter=True) == expected_ljs, \
    "Invalid JSON loaded for global config"

  jbgp_neigh_list = json.load(open(os.path.join(json_dir, "bgp-neighbor-list-ex.json"), 'r'))
  ljs = pybindJSONDecoder.load_ietf_json(jbgp_neigh_list["configuration"], ocbind, "openconfig_bgp", path_helper=yh)
  expected_ljs = \
    {
       "bgp" : {
          "neighbors" : {
             "neighbor" : {
                "13.13.13.13" : {
                   "neighbor-address" : "13.13.13.13",
                   "config" : {
                      "peer-group" : "g1"
                   }
                },
                "12.12.12.12" : {
                   "neighbor-address" : "12.12.12.12",
                   "config" : {
                      "peer-group" : "g1"
                   }
                }
             }
          }
       }
    }
  assert ljs.get(filter=True) == expected_ljs, \
    "Invalid JSON returned when loading neighbor list"

  jbgp_gr = json.load(open(os.path.join(json_dir, "bgp-gr-ex.json"), 'r'))
  ljs = pybindJSONDecoder.load_ietf_json(jbgp_gr["configuration"], ocbind, "openconfig_bgp", path_helper=yh)
  expected_ljs = \
      {
         "bgp" : {
            "neighbors" : {
               "neighbor" : {
                  "12.12.12.12" : {
                     "config" : {
                        "peer-group" : "g1"
                     },
                     "neighbor-address" : "12.12.12.12"
                  },
                  "13.13.13.13" : {
                     "neighbor-address" : "13.13.13.13",
                     "config" : {
                        "peer-group" : "g2"
                     }
                  }
               }
            }
         }
      }
  assert ljs.get(filter=True) == expected_ljs, "Graceful restart example was not loaded correctly"
  assert ljs.bgp.neighbors.neighbor[u"12.12.12.12"]._metadata == {u"inactive": True}, "Metadata for GR example was not loaded correctly"

  jbgp_deactivated = json.load(open(os.path.join(json_dir, "bgp-deactivated-config-ex.json"),'r'))
  ljs = pybindJSONDecoder.load_ietf_json(jbgp_deactivated["configuration"], ocbind, "openconfig_bgp", path_helper=yh)
  expected_ljs = \
    {
       "bgp" : {
          "global" : {
             "config" : {
                "router-id" : "10.10.10.10"
             }
          }
       }
    }
  assert ljs.get(filter=True) == expected_ljs, "Router ID configuration example not loaded correctly"
  assert ljs.bgp.global_.config.router_id._metadata["inactive"] == True, "Metadata for router-id element not set correctly"


  if not k:
    os.system("/bin/rm -rf %s/ocbind" % this_dir)

if __name__ == '__main__':
  main()
