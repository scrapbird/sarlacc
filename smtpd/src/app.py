#!/usr/bin/env python3

import asyncio
import logging
from configparser import ConfigParser

import storage
from mailer import MailHandler, CustomIdentController
from plugin_manager import PluginManager


logger = logging.getLogger()

async def amain(loop, host, port, config):
    # Init storage handlers
    store = await storage.create_storage(config, loop)

    # Init plugin manager
    plugin_manager = PluginManager()
    plugin_manager.load_plugins("plugins")
    plugin_manager.run_plugins()

    logger.info("Starting smtpd on {}:{}".format(host, port))
    try:
        cont = CustomIdentController(
                MailHandler(store, plugin_manager),
                loop=loop,
                ident_hostname=config["smtpd"]["hostname"],
                ident=config["smtpd"]["ident"],
                hostname=host,
                port=port)
        cont.start()
    except RuntimeError as e:
        logger.debug("Found an error!")


def main():
    # Read config
    config = ConfigParser()
    config.read("./smtpd.cfg")

    # Configure the logger
    logging.basicConfig(level=getattr(logging, config["logging"]["log_level"].upper()),
            format='%(levelname)s: %(asctime)s %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p')

    loop = asyncio.get_event_loop()
    loop.create_task(amain(loop=loop,
        host=config["smtpd"]["host"],
        port=config["smtpd"]["port"],
        config=config))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

