"""Fixture: Python. Not a test, only scanned by tests/test_languages.py. TODO in a docstring is not a comment."""

# TODO: plain tag with a colon
# FIXME {2030-01-02} @alice date and user
# HACK(bob): owner in parentheses
# XXX(carol) {2031-03-04} owner and date

TODO_LIST = ["TODO list", "FIXME in a string"]
text = "# TODO inside a string"
value = 1  # TODO trailing comment
message = "a" + "TODO"  # FIXME after a string with the tag
todonotifier = "not a tag"


def helper():
    """TODO in a docstring is a string, not a comment."""
    return 'say "hi" # HACK'  # TODO after an escaped quote
