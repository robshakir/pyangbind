from tests.base import PyangBindTestCase


class APITests(PyangBindTestCase):
    yang_files = ["models/simple.yang"]

    def setUp(self):
        self.simple_unchanged = self.bindings.simple()
        self.simple_changed_defaults = self.bindings.simple()
        self.simple_changed_non_defaults = self.bindings.simple()

    def test_leaf_unchanged(self):
        self.assertFalse(self.simple.test_leaf_changed.a1._changed())
        self.assertFalse(self.simple.test_leaf_changed._changed())

    def test_leaf_changed_with_defaults(self):
        self.simple_changed_defaults.test_leaf_changed.a1 = self.simple.test_leaf_changed.a1._default
        self.assertTrue(
            self.simple_changed_defaults.test_leaf_changed.a1
            == self.simple_changed_defaults.test_leaf_changed.a1._default
        )
        self.assertTrue(self.simple_changed_defaults.test_leaf_changed.a1._changed())
        self.assertTrue(self.simple_changed_defaults.test_leaf_changed._changed())

    def test_leaf_changed_with_non_defaults(self):
        self.simple_changed_non_defaults.test_leaf_changed.a1 = "test"
        self.assertTrue(self.simple_changed_non_defaults.test_leaf_changed.a1 == "test")
        self.assertTrue(self.simple_changed_non_defaults.test_leaf_changed.a1._changed())
        self.assertTrue(self.simple_changed_non_defaults.test_leaf_changed._changed())
