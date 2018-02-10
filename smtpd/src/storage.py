from base64 import b64encode, b64decode
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
import psycopg2
import aiopg
import hashlib
import time
import logging


logger = logging.getLogger()


async def create_storage(config, plugin_manager, loop):
    storage = StorageControl(config, plugin_manager, loop)
    await storage._init()
    return storage


class StorageControl:
    def __init__(self, config, plugin_manager, loop):
        self.config = config
        self.plugin_manager = plugin_manager
        self.loop = loop

        self.mongo = AsyncIOMotorClient("mongodb://{}:{}".format(
            config['mongodb']['host'],
            config['mongodb']['port']))


    async def _init(self):
        self.postgres = await self.try_connect_postgres(
                host=self.config['postgres']['host'],
                database=self.config['postgres']['database'],
                user=self.config['postgres']['user'],
                password=self.config['postgres']['password'])


    def get_sha256(self, data):
        m = hashlib.sha256()
        m.update(data)
        return m.hexdigest()


    async def try_connect_postgres(self, host, user, password, database):
        while True:
            logger.info("Trying to connect to postgres... {}@{}/{}".format(user, host, database))
            logger.debug("loop: {}".format(self.loop))
            try:
                postgres = await aiopg.connect(
                        loop=self.loop,
                        host=host,
                        user=user,
                        database=database,
                        password=password)
                logger.info("Connected")
                return postgres
            except:
                logger.warn("Failed to connect to postgres")
                time.sleep(5)


    async def store_email(self, subject, to_address_list, from_address, body, date_sent, attachments):
        logger.debug("-" * 80)
        logger.debug("Subject: {}".format(subject))
        logger.debug("to_address_list: {}".format(to_address_list))
        logger.debug("from_address: {}".format(from_address))
        logger.debug("body: {}".format(body))
        logger.debug("attachments: {}".format(attachments))
        logger.debug("date_sent: {}".format(date_sent))
        logger.debug("-" * 80)

        # async with self.postgres.cursor() as curs:
        bodySHA256 = self.get_sha256(b64encode(body.encode("utf-8")))
        curs = await self.postgres.cursor()
        logger.debug("curs: {}".format(curs))
        # insert if not existing already, otherwise return existing record
        await curs.execute('''
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
        bodyRecord = await curs.fetchone()
        bodyId = bodyRecord[0]
        logger.debug("Body ID: {}".format(bodyId))

        # add a mailitem
        await curs.execute("INSERT INTO mailitem (datesent, subject, fromaddress, bodyid) values (%s, %s, %s, %s) returning *;",
                (date_sent, subject, from_address, bodyId,))
        mailitem = await curs.fetchone()

        # inform plugins
        await self.plugin_manager.emit_new_mail_item(mailitem[0], subject, to_address_list, from_address, body, date_sent, attachments)

        # add recipients
        recipientList = []
        for recipient in to_address_list:
            # insert if not existing already, otherwise return existing record
            await curs.execute('''
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
            recipientRecord = await curs.fetchone()
            recipientList.append(recipientRecord)

            # link this recipient to the mailitem
            await curs.execute("INSERT INTO mailrecipient (recipientid, mailid) values (%s, %s);", (recipientRecord[0], mailitem[0]))

            # check if this is a new email address in the recipient list and if so, inform registered plugins
            if recipient is not recipientRecord[1]:
                # new email address
                await self.plugin_manager.emit_new_email_address(
                        _id=recipientRecord[0],
                        email_address=recipientRecord[1])


        if attachments != None:
            for attachment in attachments:
                attachmentSHA256 = self.get_sha256(b64encode(attachment["content"].encode("utf-8")))
                await curs.execute("INSERT INTO attachment (sha256, mailid, filename) values (%s, %s, %s) returning *;",
                        (attachmentSHA256, mailitem[0], attachment['fileName'],))

                attachmentRecord = await curs.fetchone()

                # check if attachment has been seen, if not store it in mongodb
                sarlacc = self.mongo['sarlacc']

                logger.info("Checking if attachment already in db")
                existing = await sarlacc["samples"].find_one({"sha256": attachmentSHA256})
                if not existing:
                    content = b64encode(attachment["content"].encode("utf-8"))
                    logger.info("Storing attachment in db")
                    await sarlacc["samples"].insert_one({
                        "sha256": attachmentSHA256,
                        "content": content})
                    logger.info("Stored file")

                    # inform plugins of new attachment
                    await self.plugin_manager.emit_new_attachment(
                            _id=attachmentRecord[0],
                            sha256=attachmentSHA256,
                            content=content)

