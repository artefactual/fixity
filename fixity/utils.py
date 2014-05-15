from uuid import UUID


def check_valid_uuid(uuid):
    """
    Checks to see if the passed string is a valid UUID.

    The passed UUID must be a string; if it is not, a TypeError is raised.

    This uses the UUID() class constructor from the uuid module,
    which raises a ValueError if the passed string is not a valid UUID.
    """
    if not isinstance(uuid, basestring):
        raise TypeError("UUID must be a string")

    UUID(uuid)
    return True
