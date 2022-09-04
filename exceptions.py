class InCompatibleTypesException(Exception):
    """Raised when two different types of data is passed for recursive update of a dictionary

    E.g. {"a": []} and {"a": {}}, Here value of key "a" is of type list and dict which are not same
    """

    pass
