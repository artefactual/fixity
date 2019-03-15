from uuid import UUID

try:
    # Python2
    STRING_TYPES = basestring
except NameError:
    # Python3
    STRING_TYPES = str


class InvalidUUID(Exception):
    def __init__(self, uuid):
        self.message = "Invalid UUID: {}".format(uuid)

    def __str__(self):
        return self.message


def check_valid_uuid(uuid):
    """
    Checks to see if the passed string is a valid UUID.

    The passed UUID must be a string; if it is not, a TypeError is raised.

    This uses the UUID() class constructor from the uuid module,
    which raises a ValueError if the passed string is not a valid UUID.
    """
    if not isinstance(uuid, STRING_TYPES):
        raise TypeError("UUID must be a string")

    try:
        UUID(uuid)
    except ValueError:
        raise InvalidUUID(uuid)

    return True
