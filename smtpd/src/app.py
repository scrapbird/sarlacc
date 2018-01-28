#!/usr/bin/env python3

import asyncio
import logging
from configparser import ConfigParser

import storage
from mailer import MailHandler, CustomIdentController
from plugin import PluginManager


logger = logging.getLogger()


async def amain(loop, host, port, store, config):
    plugin_manager = PluginManager()
    plugin_manager.load_plugins("plugins")
    plugin_manager.run_plugins()

    logger.info("Starting smtpd on {}:{}".format(host, port))
    cont = CustomIdentController(
            MailHandler(store, plugin_manager),
            ident_hostname=config["smtpd"]["hostname"],
            ident=config["smtpd"]["ident"],
            hostname=host,
            port=port)
    cont.start()


if __name__ == "__main__":
    # Read config
    config = ConfigParser()
    config.read("./smtpd.cfg")

    # Configure the logger
    logging.basicConfig(level=getattr(logging, config["logging"]["log_level"].upper()),
            format='%(levelname)s: %(asctime)s %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p')

    # Init storage handlers
    store = storage.StorageControl(config)

    loop = asyncio.get_event_loop()
    loop.create_task(amain(loop=loop,
        host=config["smtpd"]["host"],
        port=config["smtpd"]["port"],
        store=store,
        config=config))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

