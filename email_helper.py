import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from threading import Thread

"""
THIS CODE IS FROM https://github.com/ctcuff/UCFParking-Web
"""

def send_email(body, subject=f'ERROR LOG [{datetime.strftime(datetime.now(), "%b %d, %Y - %I:%M %p")}]'):
    """
    Sends an email with the subject formatted as 'ERROR LOG [Jan 01, 1970 - 12:00 AM]'
    """
    def send():
        from_ = os.environ.get('FROM')
        to = os.environ.get('TO')

        msg = MIMEMultipart()
        msg['From'] = from_
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(os.environ.get('HOST'), os.environ.get('MAIL_PORT'))
        server.starttls()
        server.login(from_, os.environ.get('PASS'))
        server.sendmail(from_, to, msg.as_string())
        server.quit()

    # Send the email on a separate thread so the server doesn't
    # have to wait for it to finish
    thread = Thread(target=send)
    thread.start()
