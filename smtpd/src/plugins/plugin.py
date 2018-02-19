class SarlaccPlugin:
    def __init__(self, logger, store):
        self.logger = logger
        self.store = store


    def run(self):
        pass


    def stop(self):
        pass


    async def new_attachment(self, _id, sha256, content, filename, tags):
        pass


    async def new_email_address(self, _id, email_address):
        pass


    async def new_mail_item(self, _id, subject, recipients, from_address, body, date_sent, attachments):
        pass
