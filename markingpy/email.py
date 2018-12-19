import mimetypes
import smtplib
from getpass import getpass
from email.message import EmailMessage


class EmailSender:

    def __init__(self, sender, username=None, server_addr = ('localhost', 461)):
        self.sender = sender
        host, port = server_addr
        if port == 587:
            server = smtplib.SMTP(host, port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(host, port)
        self.server = server
        if username is None:
            username = sender
        self.username = username
        self.messages = []

    def authenticate(self):
        password = getpass()
        self.server.login(self.username, password)
        
    def quit(self):
        self.server.quit()
    
    def create_mail(self, to, subject, body, *, 
                    cc=None, bcc=None, attach=None):
        """
        Create messages to be sent.
        """
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.sender
        msg['To'] = to
        if cc:
            cc = list(cc)
            msg['Cc'] = ' ,'.join(cc)
        if bcc:
            bcc = list(bcc)
            msg['Bcc'] = ' ,'.join(bcc)
        msg.set_content(body)

        if attach:
            for fn in attach:
                ctype, encoding = mimetypes.guess_type(fn)
                maintype, subtype = ctyle.split('/', 1)
                with open(fn, 'rb') as f:
                    msg.add_attachment(f.read(),
                                       maintype=maintype,
                                       subtype=subtype,
                                       filename=fn)

        self.messages.append(msg)

    def send_all(self):
        for msg in self.messages:
            print('Sending %s to %s' % (msg, msg['To']))
            self.server.send_message(msg)


    # context manager
    def __enter__(self):
        self.authenticate()
        return self

    def __exit__(self, *args, **kwargs):
        self.quit()



