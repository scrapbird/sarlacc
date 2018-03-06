import asyncio
import storage
import os
import pytest
from plugin_manager import PluginManager
from configparser import ConfigParser
import datetime


@pytest.yield_fixture(scope="module")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def config():
    # Read config
    config = ConfigParser()
    config.readfp(open(os.path.dirname(os.path.abspath(__file__)) + "/smtpd.cfg.default"))
    config.read(["smtpd.cfg",])
    return config


@pytest.mark.asyncio
@pytest.fixture(scope="module")
async def plugin_manager(event_loop):
    return PluginManager(event_loop)


@pytest.mark.asyncio
@pytest.fixture(scope="module")
async def store(event_loop, config, plugin_manager):
    return await storage.create_storage(config, plugin_manager, event_loop)


@pytest.mark.asyncio
async def test_create_Storage(event_loop, config, plugin_manager):
    store = await storage.create_storage(config, plugin_manager, event_loop)


@pytest.mark.asyncio
async def test_store_email(store):
    """This also doubles as a test for get_email_by_selector
    """
    now = datetime.datetime.now()
    await store.store_email(
            "test subject",
            ["test_recipient_1@example.com"],
            "from_address@example.com",
            "test body",
            now,
            [{"content": b"Test content",
                "filename": "testfile.txt"}])

    email = await store.get_email_by_selector({"date_sent": now})

    assert email["subject"] == "test subject"
    assert "test_recipient_1@example.com" == email["recipients"][0]
    assert len(email["recipients"]) == 1
    assert email["date_sent"] == now
    assert email["attachments"][0]["content"] == b"Test content"
    assert email["attachments"][0]["filename"] == "testfile.txt"

