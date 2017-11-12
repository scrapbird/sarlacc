#!/usr/bin/env python3

import asyncio
import logging
import re
import hashlib
import psycopg2
import time
from pprint import pprint
from datetime import datetime
from base64 import b64encode, b64decode
from configparser import ConfigParser

from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Sink

import email
from base64 import b64decode

from pymongo import MongoClient


def try_connect_postgres(host, user, database):
    while True:
        print("[-] Trying to connect to postgres... {}@{}/{}".format(user, host, database))
        try:
            postgres = psycopg2.connect(
                    host=host,
                    user=user,
                    database=database)
            return postgres
        except:
            print("[!] Failed to connect to postgres")
            time.sleep(5)

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
        attachments = []
        filename = None
        dateSent = datetime.now()

        # parse message
        try:
            message = email.message_from_string(envelope.content.decode("utf8", errors="replace"))
            subject = message["subject"]
            if message.is_multipart():
                for part in message.get_payload():
                    if "Content-Disposition" in part and "attachment;" in part["Content-Disposition"]:
                        matches = re.findall(r'filename=".*"', part["Content-Disposition"])
                        if len(matches) > 0:
                            a = matches[0].index('"')
                            b = matches[0].index('"', a + 1)
                            fileName = matches[0][a + 1:b]
                            content = part.get_payload()
                            attachments.append({
                                "content": content,
                                "fileName": fileName})
                    elif "Content-Type" in part and "text/plain" in part["Content-Type"]:
                        body = part.get_payload()
            else:
                # This is gross
                if "Content-Disposition" in message and "attachment;" in message["Content-Disposition"]:
                    matches = re.findall(r'filename=".*"', message["Content-Disposition"])
                    if len(matches) > 0:
                        a = matches[0].index('"')
                        b = matches[0].index('"', a + 1)
                        fileName = matches[0][a + 1:b]
                        content = message.get_payload()
                        attachments.append({
                            "content": content,
                            "fileName": fileName})
                elif "Content-Type" in message and "text/plain" in message["Content-Type"]:
                    body = message.get_payload()

            asyncio.ensure_future(store_email(
                subject = subject,
                toAddressList = toAddressList,
                fromAddress = fromAddress,
                body = body,
                attachments = attachments,
                dateSent = dateSent))

        except:
            print("crashed when parsing email.. lol")

        return "250 Message accepted for delivery"


async def store_email(subject, toAddressList, fromAddress, body, dateSent, attachments):
    print("-" * 80)
    print("Subject: {}".format(subject))
    print("toAddressList: {}".format(toAddressList))
    print("fromAddress: {}".format(fromAddress))
    print("body: {}".format(body))
    print("attachments: {}".format(attachments))
    print("dateSent: {}".format(dateSent))
    print("-" * 80)

    with postgres:
        with postgres.cursor() as curs:
            # check if body has been seen, if not store it
            bodySHA256 = get_sha256(b64encode(body.encode("utf-8")))
            curs.execute("SELECT * FROM body where sha256 = %s;", (bodySHA256,))
            bodyRecord = curs.fetchone()
            if not bodyRecord:
                # insert this body
                curs.execute("INSERT INTO body (sha256, content) values (%s, %s) returning *;",
                        (bodySHA256, body,))
                bodyRecord = curs.fetchone()
            bodyId = bodyRecord[0]
            print("Body ID: {}".format(bodyId))

            # add a mailitem
            curs.execute("INSERT INTO mailitem (dateSent, subject, bodyId) values (%s, %s, %s) returning *;",
                    (dateSent, subject, bodyId,))
            mailitem = curs.fetchone()

            if attachments != None:
                for attachment in attachments:
                    attachmentSHA256 = get_sha256(b64encode(attachment["content"].encode("utf-8")))
                    curs.execute("INSERT INTO attachment (sha256, fileName) values (%s, %s) returning *;",
                            (attachmentSHA256, attachment['fileName'],))

                    # check if attachment has been seen, if not store it in mongodb
                    sarlacc = mongo['sarlacc']

                    print("Checking if attachment already in db")
                    existing = sarlacc["attachments"].find_one({"sha256": attachmentSHA256})
                    if not existing:
                        print("Storing attachment in db")
                        sarlacc["attachments"].insert_one({
                            "sha256": attachmentSHA256,
                            "content": b64encode(attachment["content"].encode("utf-8"))})
                        print("Stored file")


async def amain(loop, host, port):
    print("[-] Starting smtpd on {}:{}".format(host, port))
    cont = Controller(MailHandler(), hostname=host, port=port)
    cont.start()


if __name__ == "__main__":
    # Read config
    config = ConfigParser()
    config.read("./smtpd.cfg")

    # init connections
    mongo = MongoClient("mongodb://{}:{}".format(
        config['mongodb']['host'],
        config['mongodb']['port']))

    postgres = try_connect_postgres(
            host=config['postgres']['host'],
            database=config['postgres']['database'],
            user=config['postgres']['user'])


    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.create_task(amain(loop=loop,
        host=config["smtpd"]["host"],
        port=config["smtpd"]["port"]))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

