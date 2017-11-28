#!/usr/bin/env python3

import asyncio
import logging
from configparser import ConfigParser

from aiosmtpd.controller import Controller
#from aiosmtpd.handlers import Sink

import storage
from mailer import MailHandler, CustomIdentController


async def amain(loop, host, port, store):
    print("[-] Starting smtpd on {}:{}".format(host, port))
    cont = CustomIdentController(Controller(MailHandler(store), hostname=host, port=port))
    cont.start()


if __name__ == "__main__":
    # Read config
    config = ConfigParser()
    config.read("./smtpd.cfg")

    # init storage handlers
    store = storage.StorageControl(config)

    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.create_task(amain(loop=loop,
        host=config["smtpd"]["host"],
        port=config["smtpd"]["port"],
        store=store))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

