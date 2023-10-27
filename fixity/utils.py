from uuid import UUID


class InvalidUUID(Exception):
    def __init__(self, uuid):
        self.message = f"Invalid UUID: {uuid}"

    def __str__(self):
        return self.message


def check_valid_uuid(uuid):
    """
    Checks to see if the passed string is a valid UUID.

    The passed UUID must be a string; if it is not, a TypeError is raised.

    This uses the UUID() class constructor from the uuid module,
    which raises a ValueError if the passed string is not a valid UUID.
    """
    if not isinstance(uuid, str):
        raise TypeError("UUID must be a string")

    try:
        UUID(uuid)
    except ValueError:
        raise InvalidUUID(uuid)

    return True
