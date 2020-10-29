#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Notify():
    """Class provides methods of notify user about event of interest"""

    def __init__(self, emailAddress: str, emailPsk: str, port: int = 465):
        self.user = {"email": emailAddress, "psk": emailPsk}
        self.port = port

    def addRecipients(self, *args):
        if not hasattr(self, "recipients"):
            self.recipients = []
        self.recipients.extend(args)

    def setSubject(self, subject: str):
        self.subject = subject

    def setBody(self, body: str):
        self.body = body

    def send(self):
        message = MIMEMultipart()
        message["From"] = self.user["email"]
        message["To"] = ", ".join(self.recipients)
        message["Subject"] = self.subject
        message.attach(MIMEText(self.body, "plain"))
        msg = message.as_string()

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtplib.gmail.com", self.port, context=context)\
                as server:
            server.login(self.user["email"], self.user["psk"])
            server.sendmail(self.user["email"], self.recipients, msg)
