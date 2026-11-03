from unittest import mock

import pytest

import digitalocean_manager
from config import Config
from digitalocean_manager import DigitalOceanManager

SUP_TAG = Config.get_supervisor_tag()


class FakeDroplet:
    def __init__(self, tags, destroy_raises=False):
        self.tags = tags
        self.name = "trigger-supervisor-test"
        self.id = 1
        self.destroy = mock.Mock(side_effect=Exception("api down") if destroy_raises else None)


@pytest.fixture
def manager_with(monkeypatch):
    def make(tags, destroy_raises=False):
        droplet = FakeDroplet(tags, destroy_raises)
        listing = [droplet]
        if not destroy_raises:
            droplet.destroy.side_effect = lambda: listing.remove(droplet)
        fake_manager = mock.Mock()
        fake_manager.get_all_droplets.side_effect = lambda: list(listing)
        monkeypatch.setattr(digitalocean_manager.digitalocean, "Manager", lambda token: fake_manager)
        return DigitalOceanManager(), droplet
    return make


def test_version_tag_format():
    assert Config.get_version_tag("v4.8.3") == "trigger-version:v4-8-3"
    assert Config.get_version_tag() == "trigger-version:v4-8-3"


def test_droplet_version_reads_tag(manager_with):
    m, d = manager_with(tags=[SUP_TAG, "trigger-version:v4-0-0"])
    assert m.droplet_version(d) == "trigger-version:v4-0-0"
    d.tags = [SUP_TAG]
    assert m.droplet_version(d) is None


def test_untagged_droplet_is_kept(manager_with):
    m, d = manager_with(tags=[SUP_TAG])
    assert m.replace_if_outdated() is True
    d.destroy.assert_not_called()


def test_same_version_is_kept(manager_with):
    m, d = manager_with(tags=[SUP_TAG, "trigger-version:v4-8-3"])
    assert m.replace_if_outdated() is True
    d.destroy.assert_not_called()


def test_other_version_is_destroyed(manager_with):
    m, d = manager_with(tags=[SUP_TAG, "trigger-version:v4-0-0"])
    assert m.replace_if_outdated() is True
    d.destroy.assert_called_once()


def test_destroy_failure_skips_create(manager_with):
    m, d = manager_with(tags=[SUP_TAG, "trigger-version:v4-0-0"], destroy_raises=True)
    assert m.replace_if_outdated() is False


def test_create_droplet_tags_version(monkeypatch, manager_with):
    m, _ = manager_with(tags=[])
    monkeypatch.setattr(m, "is_supervisor_deployed", lambda: False)
    captured = {}

    class FakeNewDroplet:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.id = 2

        def create(self):
            pass

    monkeypatch.setattr(digitalocean_manager.digitalocean, "Droplet", FakeNewDroplet)
    m.create_droplet({"TRIGGER_WORKER_TOKEN": "t", "MANAGED_WORKER_SECRET": "s",
                      "TRIGGER_API_URL": "https://x", "OTEL_EXPORTER_OTLP_ENDPOINT": "https://x/otel"})
    assert "trigger-version:v4-8-3" in captured["tags"]
    assert SUP_TAG in captured["tags"]


def test_ops_deploy_checks_version_before_early_return(monkeypatch):
    import ops_controller

    do_manager = mock.Mock()
    do_manager.replace_if_outdated.return_value = False
    monkeypatch.setattr(ops_controller, "DigitalOceanManager", lambda: do_manager)
    monkeypatch.setattr(ops_controller, "RailwayClient", lambda: mock.Mock())
    controller = ops_controller.OpsController()
    controller.config_cache = {"TRIGGER_WORKER_TOKEN": "t"}
    assert controller.deploy_supervisor() is False
    do_manager.get_deployment_info.assert_not_called()


def test_waits_until_destroyed_droplet_is_gone(monkeypatch, manager_with):
    m, d = manager_with(tags=[SUP_TAG, "trigger-version:v4-0-0"])
    listings = iter([[d], [d], [d], []])  # first call finds it, then gone after two polls
    monkeypatch.setattr(m, "get_existing_droplets", lambda: next(listings))
    monkeypatch.setattr(digitalocean_manager.time, "sleep", lambda s: None)
    assert m.replace_if_outdated() is True
    with pytest.raises(StopIteration):
        next(listings)  # all listings consumed: it polled until the droplet was gone
