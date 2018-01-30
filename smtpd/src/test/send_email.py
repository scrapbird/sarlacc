# Settings

SMTP_SERVER = 'localhost'
SMTP_PORT = 2500
SMTP_USERNAME = 'myusername'
SMTP_PASSWORD = '$uper$ecret'
SMTP_FROM = 'sender@example.com'
SMTP_TO = ['recipient@example.com', 'test@example.com']
SMTP_SUBJECT = 'testing'

TEXT_FILENAME = 'attachment.txt'
MESSAGE = """This is the message
to be sent to the client.
"""

import os
import sys
import smtplib, email
from email import encoders

TEXT_FILEPATH = os.path.dirname(os.path.abspath(__file__)) + "/" + TEXT_FILENAME

# Now construct the message
msg = email.MIMEMultipart.MIMEMultipart()
body = email.MIMEText.MIMEText(MESSAGE)
attachment = email.MIMEBase.MIMEBase('text', 'plain')
attachment.set_payload(open(TEXT_FILEPATH).read())
attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(TEXT_FILENAME))
encoders.encode_base64(attachment)
msg.attach(attachment)
msg.attach(body)
msg.add_header('From', SMTP_FROM)
msg.add_header('To', ", ".join(SMTP_TO))
msg.add_header('Subject', SMTP_SUBJECT)

# Now send the message
mailer = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
# EDIT: mailer is already connected
# mailer.connect()
# mailer.login(SMTP_USERNAME, SMTP_PASSWORD)
mailer.sendmail(SMTP_FROM, SMTP_TO, msg.as_string())
mailer.close()
print("done")
