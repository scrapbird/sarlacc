class SarlaccPlugin:
    def __init__(self, logger, store):
        """Init method for SarlaccPlugin.

        Args:
            logger -- sarlacc logger object.
            store -- sarlacc store object.
        """

        self.logger = logger
        self.store = store


    def run(self):
        """Runs the plugin.

        This method should be overridden if a plugin needs to do any initial work that isn't purely
        initialization. This could include starting any long running jobs / threads.
        """

        pass


    def stop(self):
        """Stops the plugin.

        This method should be overridden if a plugin needs to do any extra cleanup before stopping.
        This could include stopping any previously started jobs / threads.
        """

        pass


    async def new_attachment(self, _id, sha256, content, filename, tags):
        """New attachment signal.

        This method is called when a new, previously unseen attachment is detected.
        Override this method to be informed about this event.

        Args:
            _id -- the attachment postgresql record id.
            sha256 -- the sha256 hash of the attachment.
            content -- the raw file.
            filename -- the filename of the attachment.
            tags -- any tags attached to the attachment.
        """

        pass


    async def new_email_address(self, _id, email_address):
        """New email address signal.

        This method is called when a new, previously unseen recipient email address is detected.
        Override this method to be informed about this event.

        Args:
            _id -- the email address postgresql record id.
            email_address -- the email address.
        """

        pass


    async def new_mail_item(self, _id, subject, recipients, from_address, body, date_sent, attachments):
        """New email signal.

        This method is called when an email is received.
        Override this method to be informed about this event.

        Args:
            _id -- the mail item postgresql record id.
            subject -- the email subject.
            recipients -- a list of recipient email addresses.
            from_address -- the email address in the email's "from" header.
            body -- the body of the email.
            date_sent -- the date and time the email was sent.
            attachments -- a list of attachment objects in the following format:
                {
                    content: the content of the attachment (raw file),
                    filename: the name of the attachment filename
                }
        """

        pass
