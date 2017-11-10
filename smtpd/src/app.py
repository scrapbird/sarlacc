#!/usr/bin/env python3

import asyncio
import logging
import re
import hashlib
from pprint import pprint
from datetime import datetime
from base64 import b64encode, b64decode

from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Sink

import email
from base64 import b64decode

from pymongo import MongoClient


BIND_HOST = "0.0.0.0"
BIND_PORT = 8025
PSQL_HOST = "postgres"
PSQL_PORT = 5432
MNGO_HOST = "mongodb"
MNGO_PORT = 2717


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

            asyncio.ensure_future(store_email(
                subject = subject,
                toAddressList = toAddressList,
                fromAddress = fromAddress,
                body = body,
                attachment = attachment,
                filename = filename,
                dateSent = dateSent))

        return "250 Message accepted for delivery"


async def store_email(subject, toAddressList, fromAddress, body, attachment, filename, dateSent):
   # """
   #   store the following in postgres:

   #   mailitem
   #      id
   #      dateSent
   #      subjectId
   #      bodyId
   #      fileNameId
   #      attachmentId # stored in mongodb
   #   subject
   #      id
   #      content
   #   body
   #      id
   #      content
   #   filename
   #      id
   #      content
   #  """
    print('-' * 80)
    print("Subject: {}".format(subject))
    print("toAddressList: {}".format(toAddressList))
    print("fromAddress: {}".format(fromAddress))
    print("body: {}".format(body))
    print("attachment: {}".format(attachment))
    print("filename: {}".format(filename))
    print("dateSent: {}".format(dateSent))
    print('-' * 80)

    if attachment != None:
        # store attachment in mongo under key of sha256 hash of data
        mongoClient = MongoClient("mongodb://mongodb:27017")
        sarlacc = mongoClient['sarlacc']
        m = hashlib.sha256()
        m.update(b64encode(attachment.encode('utf-8')))
        k = m.hexdigest()
        sarlacc["attachments"].insert_one(k, b64encode(attachment.encode('utf-8')))
        print("Stored file")


async def amain(loop):
    cont = Controller(MailHandler(), hostname=BIND_HOST, port=BIND_PORT)
    cont.start()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.create_task(amain(loop=loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

