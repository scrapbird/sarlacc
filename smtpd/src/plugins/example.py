from plugins.plugin import SarlaccPlugin

class Plugin(SarlaccPlugin):
    def run(self):
        self.logger.info("This is an example plugin")


    async def new_attachment(self, _id, sha256, content, filename, tags):
        self.logger.info("Plugin alerting to new attachment with sha256: %s", sha256)

        # Example usage of the storage API
        attachment = await self.store.get_attachment_by_sha256(sha256)
        # attachment = {
        #     tags[]: a list of tag strings attached to this attachment,
        #     sha256: the sha256 hash of this attachment,
        #     content: the raw file,
        #     filename: the filename,
        #     _id: the id of the attachment's postgresql record
        # }


    async def new_email_address(self, _id, email_address):
        self.logger.info("Plugin alerting to new email address: %s", email_address)


    async def new_mail_item(self, _id, subject, recipients, from_address, body, date_sent, attachments):
        self.logger.info("Plugin alerting to new mail item with subject: %s", subject)
