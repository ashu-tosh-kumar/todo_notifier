import unittest

from todonotifier.languages import COMMON_EXTENSIONS, expand_extensions


class TestExpandExtensions(unittest.TestCase):
    def test_common_preset_should_have_the_agreed_extensions(self):
        self.assertEqual(
            "py js jsx ts tsx java kt go rs rb php c h cpp hpp cs swift scala sh sql yaml yml toml html css scss md".split(),
            COMMON_EXTENSIONS,
        )

    def test_common_string_should_expand_to_the_preset(self):
        self.assertEqual(COMMON_EXTENSIONS, expand_extensions("common"))

    def test_common_should_be_case_insensitive(self):
        self.assertEqual(COMMON_EXTENSIONS, expand_extensions(" Common "))

    def test_expansion_should_return_a_copy(self):
        expand_extensions("common").append("zzz")

        self.assertNotIn("zzz", COMMON_EXTENSIONS)

    def test_common_inside_a_list_should_expand_in_place_and_deduplicate(self):
        result = expand_extensions(["proto", "common", "py", "go"])

        self.assertEqual(["proto"] + COMMON_EXTENSIONS, result)

    def test_single_extension_string_should_become_a_list(self):
        self.assertEqual(["py"], expand_extensions("py"))

    def test_leading_dots_and_blanks_should_be_stripped(self):
        self.assertEqual(["py", "js"], expand_extensions([".py", "  ", "js", ".js", "..", ""]))

    def test_order_of_first_appearance_should_be_kept(self):
        self.assertEqual(["ts", "py", "js"], expand_extensions(["ts", "py", "js", "ts"]))

    def test_empty_list_should_give_an_empty_list(self):
        self.assertEqual([], expand_extensions([]))
