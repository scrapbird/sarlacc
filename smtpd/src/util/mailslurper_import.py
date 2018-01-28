#!/usr/bin/env python3

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import storage
import mysql.connector
import psycopg2
import re
from base64 import b64encode, b64decode
from configparser import ConfigParser
import asyncio


def cleanup_address(addr):
    return addr[1:len(addr)-1]


async def main():
    config = ConfigParser()
    config.read("./smtpd.cfg")


    store = storage.StorageControl(config)

    cnx = mysql.connector.connect(
            user="root", password="root",
            host="localhost",
            database="sarlacc")

    mysql_cursor = cnx.cursor()

    mysql_cursor.execute("SELECT dateSent, fromAddress, toAddressList, subject, body FROM mailitem;")

    for (dateSent, fromAddress, toAddressList, subject, body) in mysql_cursor:
        # tidy up fromAddress
        fromAddress = cleanupAddress(re.findall(r"<(.*?)>", fromAddress)[0])

        # tidy up toaAdressList
        toAddressList = re.findall(r"<(.*?)>", toAddressList)

        body = str(b64decode(body))

        store.store_email(subject, toAddressList, fromAddress, body, dateSent, [])

    mysql_cursor.close()
    cnx.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
