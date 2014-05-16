from fixity import utils

import pytest


def test_uuid_recognizes_valid_uuid():
    assert utils.check_valid_uuid('2791aed2-0fc9-4ddd-9eb1-49420ef99ef2') is True


def test_invalid_uuid_raises_valueerror():
    with pytest.raises(ValueError):
        utils.check_valid_uuid('foo')


def test_uuid_check_raises_if_not_string():
    with pytest.raises(TypeError):
        utils.check_valid_uuid({})
