#!/usr/bin/env python3

import asyncio
import logging
from pprint import pprint

from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Sink

import email
from base64 import b64decode


class MailHandler:
    async def handle_DATA(self, server, session, envelope):
        print('Message from %s' % envelope.mail_from)
        print('Message for %s' % envelope.rcpt_tos)
        print('Message data:\n')
        print(envelope.content.decode('utf8', errors='replace'))
        print('End of message')

        # parse attachments
        message = email.message_from_string(envelope.content.decode('utf8', errors='replace'))


        return '250 Message accepted for delivery'


async def amain(loop):
    cont = Controller(MailHandler(), hostname='::0', port=8025)
    cont.start()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.create_task(amain(loop=loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

