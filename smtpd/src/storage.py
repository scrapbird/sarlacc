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

        try:
            async with self.postgres.acquire() as conn:
                async with conn.cursor() as curs:
                    # create tables if they don't already exist
                    await curs.execute('''
                        CREATE TABLE body (
                                id SERIAL PRIMARY KEY,
                                sha256 text,
                                content text
                        );

                        CREATE TABLE mailitem (
                                id SERIAL PRIMARY KEY,
                                datesent timestamp,
                                subject text,
                                fromaddress text,
                                bodyid integer REFERENCES body (id)
                        );

                        CREATE TABLE recipient (
                                id SERIAL PRIMARY KEY,
                                emailaddress text
                        );

                        CREATE TABLE mailrecipient (
                                id SERIAL PRIMARY KEY,
                                recipientid integer REFERENCES recipient (id),
                                mailid integer REFERENCES mailitem (id)
                        );

                        CREATE TABLE attachment (
                                id SERIAL PRIMARY KEY,
                                mailid integer REFERENCES mailitem (id),
                                sha256 text,
                                filename text
                        );
                    ''')
                    logger.debug("Created fresh database")
        except:
            pass


    def __get_sha256(self, data):
        m = hashlib.sha256()
        m.update(data)
        return m.hexdigest()


    async def try_connect_postgres(self, host, user, password, database):
        while True:
            logger.info("Trying to connect to postgres... {}@{}/{}".format(user, host, database))
            logger.debug("loop: {}".format(self.loop))
            try:
                postgres = await aiopg.create_pool(
                        loop=self.loop,
                        host=host,
                        user=user,
                        database=database,
                        password=password)
                logger.info("Successfully connected to postgres")
                return postgres
            except:
                logger.warn("Failed to connect to postgres")
                time.sleep(5)


    async def get_attachment_by_selector(self, selector):
        sarlacc = self.mongo["sarlacc"]
        return await sarlacc["samples"].find_one(selector)


    async def get_attachment_by_id(self, _id):
        async with self.postgres.acquire() as conn:
            async with conn.cursor() as curs:
                await curs.execute('''
                        SELECT * FROM attachment
                        WHERE id=%s;
                        ''',
                        (_id,))
                attachment_record = await curs.fetchone()

                logger.info("------")
                attachment = await self.get_attachment_by_selector({"sha256": attachment_record[2]})
                logger.info(attachment)
                logger.info("------")

                return {
                    "_id": attachment_record[0],
                    "content": attachment["content"],
                    "filename": attachment["filename"],
                    "tags": attachment["tags"],
                    "sha256": attachment["sha256"]}


    async def get_attachment_by_sha256(self, sha256):
        async with self.postgres.acquire() as conn:
            async with conn.cursor() as curs:
                await curs.execute('''
                        SELECT * FROM attachment
                        WHERE sha256=%s;
                        ''',
                        (sha256,))
                attachment_record = await curs.fetchone()

                attachment = await self.get_attachment_by_selector({"sha256": attachment_record[2]})

                return {
                    "_id": attachment_record[0],
                    "content": attachment["content"],
                    "filename": attachment["filename"],
                    "tags": attachment["tags"],
                    "sha256": attachment["sha256"]}


    async def add_attachment_tag(self, sha256, tag):
        sarlacc = self.mongo["sarlacc"]
        await sarlacc["samples"].update_one({"sha256": sha256},
                {"$addToSet":
                    {"tags": tag}})

        # await attachment["tags"].update({'tags': tag}, {'$push': {'tags': new_tag}})


    async def get_email_attachments(self, email_id):
        async with self.postgres.acquire() as conn:
            async with conn.cursor() as curs:
                await curs.execute('''
                        SELECT * FROM attachment
                        WHERE mailid=%s
                        ''',
                        (email_id,))
                attachment_records = await curs.fetchall()

                attachments = []
                for record in attachment_records:
                    # Fetch the content
                    sarlacc = self.mongo["sarlacc"]
                    logger.info("Fetching attachment with sha256: %s", record[2])
                    attachment_info = await sarlacc["samples"].find_one({"sha256": record[2]})
                    attachments.append({
                        "sha256": record[2],
                        "filename": record[3],
                        "content": attachment_info["content"],
                        "tags": attachment_info["tags"]})

                return attachments


    async def get_email_by_id(self, email_id):
        async with self.postgres.acquire() as conn:
            async with conn.cursor() as curs:
                await curs.execute('''
                        SELECT * FROM mailitem
                        LEFT JOIN body ON body.id = mailitem.bodyid
                        WHERE mailitem.id=%s;
                        ''',
                        (email_id,))
                email = await curs.fetchone()
                return {
                        "id": email[0],
                        "date_sent": email[1],
                        "subject": email[2],
                        "from_address": email[3],
                        "body_id": email[4],
                        "body_sha256": email[6],
                        "body_content": email[7],
                        "attachments": await self.get_email_attachments(email_id)
                        }



    async def store_email(self, subject, to_address_list, from_address, body, date_sent, attachments):
        logger.debug("-" * 80)
        logger.debug("Subject: {}".format(subject))
        logger.debug("to_address_list: {}".format(to_address_list))
        logger.debug("from_address: {}".format(from_address))
        logger.debug("body: {}".format(body))
        logger.debug("attachments: {}".format(attachments))
        logger.debug("date_sent: {}".format(date_sent))
        logger.debug("-" * 80)

        async with self.postgres.acquire() as conn:
            bodySHA256 = self.__get_sha256(body.encode("utf-8"))
            async with conn.cursor() as curs:
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
                        attachmentSHA256 = self.__get_sha256(attachment["content"])
                        attachment["sha256"] = attachmentSHA256
                        attachment["tags"] = []
                        await curs.execute("INSERT INTO attachment (sha256, mailid, filename) values (%s, %s, %s) returning *;",
                                (attachmentSHA256, mailitem[0], attachment["filename"],))

                        attachment_record = await curs.fetchone()
                        attachment["id"] = attachment_record[0]

                        # check if attachment has been seen, if not store it in mongodb
                        sarlacc = self.mongo['sarlacc']

                        logger.info("Checking if attachment already in db")
                        existing = await sarlacc["samples"].find_one({"sha256": attachmentSHA256})
                        if existing:
                            attachment["tags"] = existing["tags"]
                        else:
                            logger.info("Storing attachment in mongodb")
                            await sarlacc["samples"].insert_one({
                                "sha256": attachmentSHA256,
                                "content": attachment["content"],
                                "filename": attachment["filename"],
                                "tags": []})
                            logger.info("Stored file")

                            # inform plugins of new attachment
                            await self.plugin_manager.emit_new_attachment(
                                    _id=attachment_record[0],
                                    sha256=attachmentSHA256,
                                    content=attachment["content"],
                                    filename=attachment["filename"],
                                    tags=[])

                # inform plugins
                await self.plugin_manager.emit_new_mail_item(mailitem[0], subject, to_address_list, from_address, body, date_sent, attachments)

