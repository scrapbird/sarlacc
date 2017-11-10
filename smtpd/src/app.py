#!/usr/bin/env python3

import asyncio
import logging
import re
from pprint import pprint
from datetime import datetime

from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Sink

import email
from base64 import b64decode


class MailHandler:
    async def handle_DATA(self, server, session, envelope):
        subject = ""
        toAddressList = envelope.rcpt_tos
        fromAddress = envelope.mail_from
        body = None
        attachment = None
        filename = None
        dateSent = datetime.now()

        # parse message
        try:
            message = email.message_from_string(envelope.content.decode('utf8', errors='replace'))
        except:
            print("crashed when parsing email.. lol")
        i = 0
        subject = message['subject']
        if message.is_multipart():
            for part in message.get_payload():
                i += 1

                if "Content-Disposition" in part and "attachment;" in part["Content-Disposition"]:
                    matches = re.findall(r'filename=".*"', part["Content-Disposition"])
                    if len(matches) > 0:
                        a = matches[0].index('"')
                        b = matches[0].index('"', a + 1)
                        filename = matches[0][a + 1:b]
                        attachment = part.get_payload()
                elif "Content-Type" in part and "text/plain" in part["Content-Type"]:
                    body = part.get_payload()

            print('-' * 80)
            print("Subject: {}".format(subject))
            print("toAddressList: {}".format(toAddressList))
            print("fromAddress: {}".format(fromAddress))
            print("body: {}".format(body))
            print("attachment: {}".format(attachment))
            print("filename: {}".format(filename))
            print("date send: {}".format(dateSent))

            print('-' * 80)

        return "250 Message accepted for delivery"


async def amain(loop):
    cont = Controller(MailHandler(), hostname='0.0.0.0', port=8025)
    cont.start()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.create_task(amain(loop=loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

