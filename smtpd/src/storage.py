from base64 import b64encode, b64decode
from pymongo import MongoClient
import psycopg2
import hashlib
import time


class StorageControl:
    def __init__(self, config):
        self.config = config

        print("host: {}".format(config['postgres']['host']))
        self.postgres = self.try_connect_postgres(
                host=config['postgres']['host'],
                database=config['postgres']['database'],
                user=config['postgres']['user'],
                password=config['postgres']['password'])

        self.mongo = MongoClient("mongodb://{}:{}".format(
            config['mongodb']['host'],
            config['mongodb']['port']))


    def get_sha256(self, data):
        m = hashlib.sha256()
        m.update(data)
        return m.hexdigest()

    def try_connect_postgres(self, host, user, password, database):
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


    async def store_email(self, subject, toAddressList, fromAddress, body, dateSent, attachments):
        print("-" * 80)
        print("Subject: {}".format(subject))
        print("toAddressList: {}".format(toAddressList))
        print("fromAddress: {}".format(fromAddress))
        print("body: {}".format(body))
        print("attachments: {}".format(attachments))
        print("dateSent: {}".format(dateSent))
        print("-" * 80)

        with self.postgres:
            with self.postgres.cursor() as curs:
                bodySHA256 = self.get_sha256(b64encode(body.encode("utf-8")))
                # insert if not existing already, otherwise return existing record
                curs.execute('''
                        WITH s AS (
                            SELECT id, sha256, content
                            FROM body
                            WHERE sha256 = %s
                        ), i as (
                            INSERT INTO body (sha256, content)
                            SELECT %s, %s
                            WHERE NOT EXISTS (SELECT 1 FROM s)
                            RETURNING id, sha256, content
                        )
                        SELECT id, sha256, content
                        FROM i
                        UNION ALL
                        SELECT id, sha256, content
                        FROM s;
                        ''',
                        (bodySHA256, bodySHA256, body,))
                bodyRecord = curs.fetchone()
                bodyId = bodyRecord[0]
                print("Body ID: {}".format(bodyId))

                # add a mailitem
                curs.execute("INSERT INTO mailitem (datesent, subject, fromaddress, bodyid) values (%s, %s, %s, %s) returning *;",
                        (dateSent, subject, fromAddress, bodyId,))
                mailitem = curs.fetchone()

                # add recipients
                recipientList = []
                for recipient in toAddressList:
                    # insert if not existing already, otherwise return existing record
                    curs.execute('''
                            WITH s AS (
                                SELECT id, emailaddress
                                FROM recipient
                                WHERE emailaddress = %s
                            ), i as (
                                INSERT INTO recipient (emailaddress)
                                SELECT %s
                                WHERE NOT EXISTS (SELECT 1 FROM s)
                                RETURNING id, emailaddress
                            )
                            SELECT id, emailaddress
                            FROM i
                            UNION ALL
                            SELECT id, emailaddress
                            FROM s;
                            ''',
                            (recipient, recipient,))
                    recipientRecord = curs.fetchone()
                    recipientList.append(recipientRecord)

                    # link this recipient to the mailitem
                    curs.execute("INSERT INTO mailrecipient (recipientid, mailid) values (%s, %s);", (recipientRecord[0], mailitem[0]))


                if attachments != None:
                    for attachment in attachments:
                        attachmentSHA256 = self.get_sha256(b64encode(attachment["content"].encode("utf-8")))
                        curs.execute("INSERT INTO attachment (sha256, mailid, filename) values (%s, %s, %s) returning *;",
                                (attachmentSHA256, mailitem[0], attachment['fileName'],))

                        # check if attachment has been seen, if not store it in mongodb
                        sarlacc = self.mongo['sarlacc']

                        print("Checking if attachment already in db")
                        existing = sarlacc["samples"].find_one({"sha256": attachmentSHA256})
                        if not existing:
                            print("Storing attachment in db")
                            sarlacc["samples"].insert_one({
                                "sha256": attachmentSHA256,
                                "content": b64encode(attachment["content"].encode("utf-8"))})
                            print("Stored file")



