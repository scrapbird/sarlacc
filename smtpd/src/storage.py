from motor.motor_asyncio import AsyncIOMotorClient
import psycopg2
import aiopg
import hashlib
import time
import logging


logger = logging.getLogger()


async def create_storage(config, plugin_manager, loop):
    """Creates and initializes a storage object.

    Args:
        plugin_manager -- sarlacc plugin_manager object.
        loop -- asyncio loop.

    Returns:
        The storage object.
    """

    storage = StorageControl(config, plugin_manager, loop)
    await storage._init()
    return storage


class StorageControl:
    def __init__(self, config, plugin_manager, loop):
        """Init method for StorageControl class.

        Args:
            config -- sarlacc config object
            plugin_manager -- sarlacc plugin_manager object
            loop -- asyncio loop
        """

        self.config = config
        self.plugin_manager = plugin_manager
        self.loop = loop

        self.mongo = AsyncIOMotorClient("mongodb://{}:{}".format(
            config['mongodb']['host'],
            config['mongodb']['port']))


    async def _init(self):
        """Async init method to be called once inside event loop.

        Used to initialize postgres so we can await on the connect method.
        """

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


    async def __get_sha256(self, data):
        """Calculate sha256 hash of data.

        Args:
            data -- the data to hash.

        Returns:
            The sha256 hash.
        """

        m = hashlib.sha256()
        m.update(data)
        return m.hexdigest()


    async def try_connect_postgres(self, host, user, password, database):
        """Loop forever and attempt to connect to postgres.

        Args:
            host -- the hostname to connect to.
            user -- the username to authenticate as.
            password -- the password to authenticate with.
            database -- the name of the database to use.

        Returns:
            The connected postgres client.
        """

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
        """Gets an attachment using a mongodb query.

        Args:
            selector -- a query object for mongodb as documented here: https://docs.mongodb.com/manual/reference/method/db.collection.findOne/

        Returns:
            The attachment object in the following format:
                {
                    tags[]: a list of tag strings attached to this attachment,
                    sha256: the sha256 hash of this attachment,
                    content: the raw file,
                    filename: the filename,
                    _id: the id of the attachment's postgresql record
                }
        """

        sarlacc = self.mongo["sarlacc"]
        return await sarlacc["samples"].find_one(selector)


    async def get_attachment_by_id(self, _id):
        """Gets an attachment by it's id.

        Args:
            _id -- the id of the attachment.

        Returns:
            The attachment object in the following format:
                {
                    tags[]: a list of tag strings attached to this attachment,
                    sha256: the sha256 hash of this attachment,
                    content: the raw file,
                    filename: the filename,
                    _id: the id of the attachment's postgresql record
                }
        """

        async with self.postgres.acquire() as conn:
            async with conn.cursor() as curs:
                await curs.execute('''
                        SELECT * FROM attachment
                        WHERE id=%s;
                        ''',
                        (_id,))
                attachment_record = await curs.fetchone()

                attachment = await self.get_attachment_by_selector({"sha256": attachment_record[2]})

                return {
                    "_id": attachment_record[0],
                    "content": attachment["content"],
                    "filename": attachment["filename"],
                    "tags": attachment["tags"],
                    "sha256": attachment["sha256"]}


    async def get_attachment_by_sha256(self, sha256):
        """Gets an attachment by it's sha256 hash.

        Args:
            sha256 -- the hash to search for.

        Returns:
            The attachment object in the following format:
                {
                    tags[]: a list of tag strings attached to this attachment,
                    sha256: the sha256 hash of this attachment,
                    content: the raw file,
                    filename: the filename,
                    _id: the id of the attachment's postgresql record
                }
        """

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
        """Adds a tag to an attachment.

        Args:
            sha256 -- the hash of the attachment to tag.
            tag -- the string to tag it with.
        """

        sarlacc = self.mongo["sarlacc"]
        await sarlacc["samples"].update_one(
                {"sha256": sha256},
                {"$addToSet":
                    {"tags": tag}})


    async def get_email_attachments(self, email_id, content=True):
        """Gets an email's attachments.

        Args:
            email_id -- the id of the mailitem to get attachments for.
            content (boolean) -- set this to False to omit the attachment's actual file content.
                Defaults to True.

        Returns:
            A list of email attachment objects in the following format:
                [{
                    tags[]: a list of tag strings attached to this attachment,
                    sha256: the sha256 hash of this attachment,
                    content: the raw file,
                    filename: the filename,
                    _id: the id of the attachment's postgresql record
                }]
        """

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

                    if content:
                        attachment_info = await sarlacc["samples"].find_one({"sha256": record[2]})
                        attachments.append({
                            "_id": record[0],
                            "sha256": record[2],
                            "filename": record[3],
                            "content": attachment_info["content"],
                            "tags": attachment_info["tags"]})
                    else:
                        attachment_info = await sarlacc["samples"].find_one({"sha256": record[2]},
                                {"tags": True})
                        attachments.append({
                            "_id": record[0],
                            "sha256": record[2],
                            "filename": record[3],
                            "tags": attachment_info["tags"]})

                return attachments


    async def get_email_recipients(self, email_id):
        """Gets an email's recipients.

        Args:
            email_id -- the id of the mailitem to get recipients for.

        Returns:
            A list of email recipients
                ["user@example.com", ...]
        """
        async with self.postgres.acquire() as conn:
            async with conn.cursor() as curs:
                await curs.execute('''
                        SELECT * FROM mailrecipient
                        LEFT JOIN recipient on recipient.id = mailrecipient.recipientid
                        WHERE mailrecipient.mailid=%s
                        ''',
                        (email_id,))
                recipient_records = await curs.fetchall()

                recipients = []
                for record in recipient_records:
                    recipients.append(record[4])

                return recipients


    async def get_email_by_selector(self, selector, attachment_content=True):
        """Get email by sql query.

        Gets a mail item using a selector object.

        Args:
            selector -- a dict containing values to query for in the following format:
                {
                    "column_name_0": value,
                    "column_name_1": value
                    ...
                    "column_name_n": value
                }
                Where "column_name" is the name of the column and value is the value you search
                for in the `where` clause of the sql query.
            attachment_content (boolean): set to false to not return actual file content for attachments.
                This is useful if the file is very large. Defaults to True.

        Returns:
            An email object in the following format:
                {
                    _id: the id of the email record in postgres,
                    date_send: the date and time the email was sent,
                    subject: the email subject,
                    from_address: the email address in the from header,
                    recipients: the list of recipient email addresses
                    body_id: the id of the body record in postgres,
                    body_sha256: the sha256 hash of the body,
                    body_content: the content of the body,
                    attachments: a list of email attachment objects in the following format:
                    Note: to get attachment content see the get_email_attachments method.
                        [{
                            tags[]: a list of tag strings attached to this attachment,
                            sha256: the sha256 hash of this attachment,
                            filename: the filename,
                            _id: the id of the attachment's postgresql record
                        }]
                }

        Example:
            Lets say I wish to get an email that has the subject "test" and the sending email
            address "from@example.com", simply use the following:
                {"subject": "test", "from_address": "from@example.com"}
        """

        # A list of selector keys matched with the full column name they represent and their value
        # (defaults to None)
        #
        # This also doubles as a whitelist for column names allowed in the query to prevent sqli.
        whitelist_columns = {
                "_id": "mailitem.id",
                "date_sent": "mailitem.datesent",
                "subject": "mailitem.subject",
                "from_address": "mailitem.fromaddress",
                "body_id": "mailitem.bodyid",
                "body_sha256": "body.sha256",
                "body_content": "body.content"}

        and_operator = False
        query_string = """SELECT * FROM mailitem
                LEFT JOIN body ON body.id = mailitem.bodyid """

        values = ()

        # Loop over values and add them to the query if they're whitelisted
        for key, value in selector.items():
            if key in whitelist_columns:
                if not and_operator:
                    and_operator = True
                    query_string += "WHERE "
                else:
                    query_string += "AND "
                query_string += whitelist_columns[key] + "=%s "
                values = values + (value,)
            else:
                logger.warning("Detected selector key not specified in the whitelist. Key: %s", key)

        query_string += ";"

        async with self.postgres.acquire() as conn:
            async with conn.cursor() as curs:

                await curs.execute(query_string,
                        values)
                email = await curs.fetchone()

                return {
                        "_id": email[0],
                        "date_sent": email[1],
                        "subject": email[2],
                        "from_address": email[3],
                        "recipients": await self.get_email_recipients(email[0]),
                        "body_id": email[4],
                        "body_sha256": email[6],
                        "body_content": email[7],
                        "attachments": await self.get_email_attachments(email[0])
                        }



    async def get_email_by_id(self, email_id):
        """Get email by id.

        Gets a mail item by it's id.

        Args:
            email_id -- the id of the mail item.

        Returns:
            An email object in the following format:
                {
                    _id: the id of the email record in postgres,
                    date_send: the date and time the email was sent,
                    subject: the email subject,
                    from_address: the email address in the from header,
                    body_id: the id of the body record in postgres,
                    body_sha256: the sha256 hash of the body,
                    body_content: the content of the body,
                    attachments: a list of email attachment objects in the following format:
                        [{
                            tags[]: a list of tag strings attached to this attachment,
                            sha256: the sha256 hash of this attachment,
                            content: the raw file,
                            filename: the filename,
                            _id: the id of the attachment's postgresql record
                        }]
                }
        """

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
                        "_id": email[0],
                        "date_sent": email[1],
                        "subject": email[2],
                        "from_address": email[3],
                        "recipients": await self.get_email_recipients(email[0]),
                        "body_id": email[4],
                        "body_sha256": email[6],
                        "body_content": email[7],
                        "attachments": await self.get_email_attachments(email_id)
                        }



    async def store_email(self, subject, to_address_list, from_address, body, date_sent, attachments):
        """A new email item.

        Args:
            subject -- the subject of the email.
            to_address_list -- a list of recipient email addresses.
            from_address -- the email address in the from header.
            body -- the email body.
            date_send -- the date and time the email was sent.
            attachments -- a list of attachment objects in the following format:
                {
                    content: the content of the attachment (raw file),
                    filename: the name of the attachment filename
                }
        """

        logger.debug("-" * 80)
        logger.debug("Subject: %s", subject)
        logger.debug("to_address_list: %s", to_address_list)
        logger.debug("from_address: %s", from_address)
        logger.debug("body: %s", body)
        logger.debug("attachment count: %s", len(attachments))
        logger.debug("date_sent: %s", date_sent)
        logger.debug("-" * 80)

        async with self.postgres.acquire() as conn:
            body_sha256 = await self.__get_sha256(body.encode("utf-8"))
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
                        (body_sha256, body_sha256, body,))
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
                        attachment_sha256 = await self.__get_sha256(attachment["content"])
                        attachment["sha256"] = attachment_sha256
                        attachment["tags"] = []
                        await curs.execute("INSERT INTO attachment (sha256, mailid, filename) values (%s, %s, %s) returning *;",
                                (attachment_sha256, mailitem[0], attachment["filename"],))

                        attachment_record = await curs.fetchone()
                        attachment["id"] = attachment_record[0]

                        # check if attachment has been seen, if not store it in mongodb
                        sarlacc = self.mongo['sarlacc']

                        logger.info("Checking if attachment already in db")
                        write_result = await sarlacc["samples"].update(
                                {"sha256": attachment_sha256},
                                {
                                    "sha256": attachment_sha256,
                                    "content": attachment["content"],
                                    "filename": attachment["filename"],
                                    "tags": []
                                },
                                True)

                        if not write_result["updatedExisting"]:
                            # inform plugins of new attachment
                            await self.plugin_manager.emit_new_attachment(
                                    _id=attachment_record[0],
                                    sha256=attachment_sha256,
                                    content=attachment["content"],
                                    filename=attachment["filename"],
                                    tags=[])

                # inform plugins
                await self.plugin_manager.emit_new_mail_item(mailitem[0], subject, to_address_list, from_address, body, date_sent, attachments)

