from tests.base import PyangBindTestCase


class APITests(PyangBindTestCase):
    yang_files = ['models/simple.yang']

    def setUp(self):
        self.simple = self.bindings.simple()

    def test_leaf_changed(self):
        assert not self.simple.test_leaf_changed.a1._changed()
        assert not self.simple.test_leaf_changed._changed()

        self.simple.test_leaf_changed.a1 = self.simple.test_leaf_changed.a1._default
        assert self.simple.test_leaf_changed.a1 == self.simple.test_leaf_changed.a1._default
        assert self.simple.test_leaf_changed.a1._changed()
        assert self.simple.test_leaf_changed._changed()

        self.simple.test_leaf_changed.a1 = "test"
        assert self.simple.test_leaf_changed.a1 == "test"
        assert self.simple.test_leaf_changed.a1._changed()
        assert self.simple.test_leaf_changed._changed()
