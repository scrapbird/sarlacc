import email
import re
import asyncio
import logging
import functools
from datetime import datetime
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP as Server
from base64 import b64decode
import storage


logger = logging.getLogger()


async def create_mailer(handler, loop, ident_hostname, ident, **kwargs):
    mailer = Mailer(handler, loop, ident_hostname, ident, **kwargs)
    return mailer


class CustomIdentController(Controller):
    def __init__(self, handler, loop, ident_hostname, ident, **kwargs):
        self.loop = loop
        self.ident_hostname = ident_hostname
        self.ident = ident
        super(CustomIdentController, self).__init__(handler, loop=loop, **kwargs)

    def factory(self):
        server = Server(self.handler)
        server.hostname = self.ident_hostname
        server.__ident__ = self.ident
        return server


class MailHandler:
    def __init__(self, loop, config, plugin_manager):
        self.loop = loop
        self.config = config
        self.plugin_manager = plugin_manager
        loop.create_task(self.init_store())


    async def init_store(self):
        # Init storage handlers
        self.store = await storage.create_storage(self.config, self.plugin_manager, self.loop)

        self.plugin_manager.load_plugins(self.store, "plugins")
        self.plugin_manager.run_plugins()


    async def handle_DATA(self, server, session, envelope):
        subject = ""
        to_address_list = envelope.rcpt_tos
        from_address = envelope.mail_from
        body = None
        attachments = []
        date_sent = datetime.now()

        # Parse message
        try:
            message = email.message_from_string(envelope.content.decode("utf8", errors="replace"))
            subject = message["subject"]
            if message.is_multipart():
                for part in message.get_payload():
                    if "Content-Disposition" in part and "attachment;" in part["Content-Disposition"]:
                        filename = None
                        matches = re.findall(r'filename=".*"', part["Content-Disposition"])
                        if len(matches) > 0:
                            a = matches[0].index('"')
                            b = matches[0].index('"', a + 1)
                            filename = matches[0][a + 1:b]
                            content = part.get_payload()

                            # Check if attachment is base64 encoded
                            if "Content-Transfer-Encoding" in part and "base64" in part["Content-Transfer-Encoding"]:
                                content = b64decode(content.strip())

                            attachments.append({
                                "content": content,
                                "filename": filename})
                    elif "Content-Type" in part and "text/plain" in part["Content-Type"]:
                        body = part.get_payload()
                    elif "Content-Type" in part and "text/html" in part["Content-Type"]:
                        body = part.get_payload()
            else:
                # This is gross
                if "Content-Disposition" in message and "attachment;" in message["Content-Disposition"]:
                    filename = None
                    matches = re.findall(r'filename=".*"', message["Content-Disposition"])
                    if len(matches) > 0:
                        a = matches[0].index('"')
                        b = matches[0].index('"', a + 1)
                        filename = matches[0][a + 1:b]
                        content = message.get_payload()

                        # Check if attachment is base64 encoded
                        if "Content-Transfer-Encoding" in part and "base64" in part["Content-Transfer-Encoding"]:
                            content = b64decode(content.strip())

                        attachments.append({
                            "content": content,
                            "filename": filename})
                elif "Content-Type" in message and "text/plain" in message["Content-Type"]:
                    body = message.get_payload()
                elif "Content-Type" in message and "text/html" in message["Content-Type"]:
                    body = message.get_payload()

            asyncio.ensure_future(self.store.store_email(
                subject = subject,
                to_address_list = to_address_list,
                from_address = from_address,
                body = body,
                attachments = attachments,
                date_sent = date_sent))

        except:
            logger.error("Failed to parse mail")
            e = sys.exc_info()[0]
            logger.error(e)

        return "250 Message accepted for delivery"
