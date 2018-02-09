#!/usr/bin/env python3

import asyncio
import threading
import sys
import logging
from configparser import ConfigParser

from mailer import MailHandler, CustomIdentController
from plugin_manager import PluginManager


logger = logging.getLogger()

def main():
    # Read config
    config = ConfigParser()
    config.read("./smtpd.cfg")

    # Configure the logger
    logging.basicConfig(level=getattr(logging, config["logging"]["log_level"].upper()),
            format='%(levelname)s: %(asctime)s %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p')

    loop = asyncio.get_event_loop()

    # Init plugin manager
    plugin_manager = PluginManager(loop)
    plugin_manager.load_plugins("plugins")
    plugin_manager.run_plugins()

    logger.info("Starting smtpd on {}:{}".format(config["smtpd"]["host"], config["smtpd"]["port"]))
    cont = CustomIdentController(
            MailHandler(loop, config, plugin_manager),
            loop=loop,
            ident_hostname=config["smtpd"]["hostname"],
            ident=config["smtpd"]["ident"],
            hostname=config["smtpd"]["host"],
            port=config["smtpd"]["port"])
    cont.start()

    # Ugly but whatever, wait until the controller thread finishes (wtf why do they start a thread)
    threads = threading.enumerate()
    for thread in threads:
        if not threading.current_thread() == thread:
            thread.join()


if __name__ == "__main__":
    main()

