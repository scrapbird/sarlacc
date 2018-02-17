from plugins.plugin import SarlaccPlugin

class Plugin(SarlaccPlugin):
    def run(self):
        self.logger.info("This is an example plugin")


    async def new_attachment(self, _id, sha256, content):
        self.logger.info("Plugin alerting to new attachment with sha256: %s", sha256)


    async def new_email_address(self, _id, email_address):
        self.logger.info("Plugin alerting to new email address: %s", email_address)


    async def new_mail_item(self, _id, subject, recipients, from_address, body, date_sent, attachments):
        self.logger.info("Plugin alerting to new mail item with subject: %s", subject)

        mailitem = await self.store.get_email_by_id(_id)
