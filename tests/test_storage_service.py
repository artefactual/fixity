import json

from fixity import storage_service
from fixity.models import Session
from fixity.utils import InvalidUUID

import pytest
import vcr


SESSION = Session()
STORAGE_SERVICE_URL = 'http://localhost:8000/'


### Single AIP

@vcr.use_cassette('fixtures/vcr_cassettes/single_aip.yaml')
def test_get_single_aip():
    aip_uuid = 'a7f2a05b-0fdf-42f1-a46c-4522a831cf17'
    aip = storage_service.get_single_aip(aip_uuid, STORAGE_SERVICE_URL)
    assert type(aip) == dict
    assert aip['uuid'] == aip_uuid


@vcr.use_cassette('fixtures/vcr_cassettes/single_aip_404.yaml')
def test_single_aip_raises_on_404():
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_single_aip('ba31d9b8-5baa-4d62-839e-cf71497d4acf', STORAGE_SERVICE_URL)

    assert "returned 404" in ex.value.message
    assert ex.value.report is None


@vcr.use_cassette('fixtures/vcr_cassettes/single_aip_500.yaml')
def test_single_aip_raises_on_500():
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_single_aip('a7f2a05b-0fdf-42f1-a46c-4522a831cf17', STORAGE_SERVICE_URL)

    assert "internal error" in ex.value.message
    assert ex.value.report is None


@vcr.use_cassette('fixtures/vcr_cassettes/single_aip_504.yaml')
def test_single_aip_raises_on_504():
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_single_aip('a7f2a05b-0fdf-42f1-a46c-4522a831cf17', STORAGE_SERVICE_URL)

    assert "gateway timeout" in ex.value.message
    assert ex.value.report is None


def test_single_aip_raises_with_invalid_uuid():
    with pytest.raises(InvalidUUID):
        storage_service.get_single_aip('foo', STORAGE_SERVICE_URL)


def test_single_aip_raises_with_invalid_url():
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_single_aip('a7f2a05b-0fdf-42f1-a46c-4522a831cf17', "http://foo")

    assert "Unable to connect" in ex.value.message


### All AIPs

@vcr.use_cassette('fixtures/vcr_cassettes/all_aips.yaml')
def test_get_all_aips():
    aip_uuids = ('a7f2a05b-0fdf-42f1-a46c-4522a831cf17', 'c8ebb75e-6b7a-46dd-a360-91d3753d7b72')

    aips = storage_service.get_all_aips(STORAGE_SERVICE_URL)
    assert len(aips) == 2
    for aip in aips:
        assert type(aip) == dict
        assert aip['uuid'] in aip_uuids


@vcr.use_cassette('fixtures/vcr_cassettes/all_aips_500.yaml')
def test_get_all_aips_raises_on_500():
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_all_aips(STORAGE_SERVICE_URL)

    assert "internal error" in ex.value.message
    assert ex.value.report is None


@vcr.use_cassette('fixtures/vcr_cassettes/all_aips_504.yaml')
def test_get_all_aips_raises_on_504():
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_all_aips(STORAGE_SERVICE_URL)

    assert "gateway timeout" in ex.value.message
    assert ex.value.report is None


def test_get_all_aips_raises_with_invalid_url():
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.get_all_aips("http://foo")

    assert "Unable to connect" in ex.value.message


### Fixity scan

@vcr.use_cassette('fixtures/vcr_cassettes/fixity_success.yaml')
def test_successful_fixity_scan():
    success, report = storage_service.scan_aip('c8ebb75e-6b7a-46dd-a360-91d3753d7b72', STORAGE_SERVICE_URL, SESSION)

    assert success is True
    assert report.success is True

    parsed_report = json.loads(report.report)
    for category in ('untracked', 'changed', 'missing'):
        assert len(parsed_report['failures']['files'][category]) == 0


@vcr.use_cassette('fixtures/vcr_cassettes/fixity_fail.yaml')
def test_failed_fixity_scan():
    success, report = storage_service.scan_aip('c8ebb75e-6b7a-46dd-a360-91d3753d7b72', STORAGE_SERVICE_URL, SESSION)
    assert success is False
    assert report.success is False

    parsed_report = json.loads(report.report)
    assert len(parsed_report['failures']['files']['changed']) == 2
    assert parsed_report['failures']['files']['changed'][0]['path'] == 'data/objects/oakland03.jp2'
    for category in ('untracked', 'missing'):
        assert len(parsed_report['failures']['files'][category]) == 0


@vcr.use_cassette('fixtures/vcr_cassettes/fixity_500.yaml')
def test_fixity_scan_raises_on_500():
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.scan_aip('a7f2a05b-0fdf-42f1-a46c-4522a831cf17', STORAGE_SERVICE_URL, SESSION)

    assert "internal error" in ex.value.message


def test_fixity_scan_raises_on_invalid_url():
    with pytest.raises(storage_service.StorageServiceError) as ex:
        storage_service.scan_aip('a7f2a05b-0fdf-42f1-a46c-4522a831cf17', "http://foo", SESSION)

    assert "Unable to connect" in ex.value.message
