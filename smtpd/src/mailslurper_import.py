#!/usr/bin/env python3

import storage

import mysql.connector
import psycopg2
from base64 import b64encode, b64decode
from configparser import ConfigParser

import storage

config = ConfigParser()
config.read("./smtpd.cfg")

store = storage.StorageControl(config)

mysql = mysql.connector.connect(
        user="root", password="root",
        host="localhost",
        database="sarlacc")

mysql_cursor = cnx.cursor()

mysql_cursor.execute("SELECT dateSent, fromAddress, toAddressList, subject, body FROM mailitem limit 1;")

for (dateSent, fromAddress, toAddressList, subject, body) in cursor:
    # tidy up fromAddress
    fromAddress = re.findone(r"<.*>", fromAddress)
    print("fromAddress: {}".fromAddress)

    # tidy up toaAdressList
    toAddressList = re.findall(r"<.*>; ", toAddressList)
    print("toAddressList: {}".toAddressList)

    body = b64decode(body)

    store.store_email(subject, toAddressList, fromAddress, body, dateSent, [])

mysql_cursor.close()
mysql.close()

