#!/usr/bin/env python3

import storage

import mysql.connector
import psycopg2
import re
from base64 import b64encode, b64decode
from configparser import ConfigParser

import storage


def cleanupAddress(addr):
    return addr[1:len(addr)-1]

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
    print("fromAddress: {}".format(fromAddress))

    # tidy up toaAdressList
    toAddressList = re.findall(r"<(.*?)>", toAddressList)
    print("toAddressList: {}".format(toAddressList))

    body = b64decode(body)

    store.store_email(subject, toAddressList, fromAddress, body, dateSent, [])

mysql_cursor.close()
cnx.close()

