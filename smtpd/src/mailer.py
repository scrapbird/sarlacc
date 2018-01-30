import email
import re
import asyncio
import logging
from datetime import datetime
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP as Server


logger = logging.getLogger()


async def create_mailer(handler, loop, ident_hostname, ident, **kwargs):
    mailer = Mailer(handler, loop, ident_hostname, ident, **kwargs)
    await mailer._init()
    return mailer


class CustomIdentController(Controller):
    def __init__(self, handler, loop, ident_hostname, ident, **kwargs):
        self.loop = loop
        self.ident_hostname = ident_hostname
        self.ident = ident
        super(CustomIdentController, self).__init__(handler, loop=loop, **kwargs)

    async def _init():
        pass

    def factory(self):
        server = Server(self.handler)
        server.hostname = self.ident_hostname
        server.__ident__ = self.ident
        return server


class MailHandler:
    def __init__(self, store, plugin_manager):
        self.store = store
        self.plugin_manager = plugin_manager


    async def handle_DATA(self, server, session, envelope):
        subject = ""
        toAddressList = envelope.rcpt_tos
        fromAddress = envelope.mail_from
        body = None
        attachments = []
        filename = None
        dateSent = datetime.now()

        # Parse message
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
                    elif "Content-Type" in part and "text/html" in part["Content-Type"]:
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
                elif "Content-Type" in message and "text/html" in message["Content-Type"]:
                    body = message.get_payload()

            asyncio.ensure_future(self.store.store_email(
                subject = subject,
                toAddressList = toAddressList,
                fromAddress = fromAddress,
                body = body,
                attachments = attachments,
                dateSent = dateSent))

        except:
            logger.error("Failed to parse mail")
            e = sys.exc_info()[0]
            logger.error(e)

        return "250 Message accepted for delivery"
