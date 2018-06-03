import os

try:
    import unittest2 as unittest
except ImportError:
    import unittest


def test_suite():
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover("tests", pattern="run.py")
    return test_suite
