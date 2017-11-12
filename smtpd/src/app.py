#!/usr/bin/env python3

# TODO Handle multiple attachments

import asyncio
import logging
import re
import hashlib
import psycopg2
from pprint import pprint
from datetime import datetime
from base64 import b64encode, b64decode
from configparser import ConfigParser

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


# init connections
mongo = MongoClient("mongodb://mongodb:27017")
postgres = psycopg2.connect(
        host="postgres",
        database="sarlacc",
        user="postgres")


def get_sha256(data):
    m = hashlib.sha256()
    m.update(data)
    return m.hexdigest()


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
                        fileName = matches[0][a + 1:b]
                        attachment = part.get_payload()
                elif "Content-Type" in part and "text/plain" in part["Content-Type"]:
                    body = part.get_payload()

            asyncio.ensure_future(store_email(
                subject = subject,
                toAddressList = toAddressList,
                fromAddress = fromAddress,
                body = body,
                attachment = attachment,
                fileName = fileName,
                dateSent = dateSent))

        return "250 Message accepted for delivery"


async def store_email(subject, toAddressList, fromAddress, body, attachment, fileName, dateSent):
    print('-' * 80)
    print("Subject: {}".format(subject))
    print("toAddressList: {}".format(toAddressList))
    print("fromAddress: {}".format(fromAddress))
    print("body: {}".format(body))
    print("attachment: {}".format(attachment))
    print("fileName: {}".format(fileName))
    print("dateSent: {}".format(dateSent))
    print('-' * 80)

    with postgres:
        with postgres.cursor() as curs:
            # check if body has been seen, if not store it
            bodySHA256 = get_sha256(b64encode(body.encode('utf-8')))
            curs.execute("SELECT * FROM body where sha256 = %s;", (bodySHA256,))
            results = curs.fetchall()
            if not results:
                # insert this body
                curs.execute("INSERT INTO body (sha256, content) values (%s, %s) returning *;",
                        (bodySHA256, body,))
                results = curs.fetchone()
                print(results)
            bodyId = results[0]
            print("Body ID: {}".format(bodyId))

            # add a mailitem
            curs.execute("INSERT INTO mailitem (dateSent, subject, bodyId) values (%s, %s, %s) returning *;",
                    (dateSent, subject, bodyId,))
            mailitem = curs.fetchone()

            if attachment != None:
                attachmentSHA256 = get_sha256(b64encode(attachment.encode('utf-8')))
                curs.execute("INSERT INTO attachment (sha256, fileName) values (%s, %s) returning *;",
                        (attachmentSHA256, fileName,))

                # check if attachment has been seen, if not store it in mongodb
                sarlacc = mongo['sarlacc']

                print("Checking if attachment already in db")
                existing = sarlacc["attachments"].find_one({"sha256": attachmentSHA256})
                if not existing:
                    print("Storing attachment in db")
                    sarlacc["attachments"].insert_one({
                        "sha256": attachmentSHA256,
                        "content": b64encode(attachment.encode('utf-8'))})
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

