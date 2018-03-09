try:
  import unittest2 as unittest
except ImportError:
  import unittest


def test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='run.py')
    return test_suite
