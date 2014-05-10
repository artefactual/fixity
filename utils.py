from uuid import UUID


def check_valid_uuid(uuid):
    """
    Checks to see if the passed string is a valid UUID.

    This uses the UUID() class constructor from the uuid module,
    which raises a ValueError if the passed string is not a valid UUID.
    """
    UUID(uuid)
    return True
