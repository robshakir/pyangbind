import distutils
import inspect
import os.path
import subprocess
import types
try:
  import unittest2 as unittest
except ImportError:
  import unittest


class PyangBindTestCase(unittest.TestCase):
  yang_files = None
  pyang_flags = []

  @classmethod
  def setUpClass(cls):
    if cls.yang_files is None:
      raise ValueError("cls.yang_files must be set")
    pyang_path = distutils.spawn.find_executable('pyang')
    if not pyang_path:
      raise RuntimeError("Could not locate `pyang` executable.")
    base_dir = os.path.dirname(os.path.dirname(__file__))
    test_path = os.path.dirname(inspect.getfile(cls))
    yang_files = [os.path.join(test_path, filename) for filename in cls.yang_files]
    plugin_dir = os.path.join(base_dir, 'pyangbind', 'plugin')

    pyang_cmd = "{pyang} --plugindir {plugins} -f pybind -p {test_path} {flags} {yang_files}".format(
      pyang=pyang_path,
      plugins=plugin_dir,
      test_path=test_path,
      flags=' '.join(cls.pyang_flags),
      yang_files=' '.join(yang_files)
    )
    bindings_code = subprocess.check_output(
      pyang_cmd, shell=True, stderr=subprocess.STDOUT, env={'PYTHONPATH': base_dir}
    )
    cls.bindings = types.ModuleType('bindings')
    exec(bindings_code, cls.bindings.__dict__)

  @classmethod
  def tearDownClass(cls):
    del cls.bindings
