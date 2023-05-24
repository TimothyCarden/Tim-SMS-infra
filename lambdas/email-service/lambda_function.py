import base64
import json
import logging
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3
from jinja2 import Environment

from s3_template_loader import S3loader

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

templates_bucket_name = os.environ['TEMPLATES_BUCKET_NAME']
templates_folder = os.environ['TEMPLATES_FOLDER']

s3_client = boto3.client('s3')
ses_client = boto3.client('ses')

env = Environment(loader=S3loader(templates_bucket_name, templates_folder))


def download_file(bucket_name, file_url):
    obj = s3_client.get_object(
        Bucket=bucket_name, Key=file_url
    )
    return obj


def send_email(raw_message):
    message = json.loads(raw_message)

    email_message = MIMEMultipart()
    email_message['Subject'] = message['subject']
    email_message['From'] = message['participants']['from']
    email_message['To'] = ','.join(message['participants']['to'])
    if 'cc' in message['participants']:
        email_message['CC'] = ','.join(message['participants']['cc'])

    # message body
    part = MIMEText(get_email_body(message), 'html')
    email_message.attach(part)

    if 'attachments' in message:
        for attachment in message['attachments']:
            email_message.attach(get_attachment(attachment))

    result = ses_client.send_raw_email(Source=email_message['From'],
                                       Destinations=message['participants']['to'] + (
                                           message['participants']['cc'] if 'cc' in message[
                                               'participants'] else []),
                                       RawMessage={'Data': email_message.as_string(), })
    logger.info(result)


def get_attachment(attachment):
    head, tail = os.path.split(attachment['file_url'])
    filename = tail if not attachment['extension'] else tail + f'.{attachment["extension"]}'
    file = download_file(attachment['bucket_name'], attachment['file_url'])
    part = MIMEApplication(file['Body'].read())
    part.add_header('Content-Disposition', 'attachment', filename=filename)
    return part


def get_email_body(message):
    template = env.get_template(message['type'] + '.html')
    return template.render(message['body']['content'])


def lambda_handler(event, context):
    logger.info(event)
    if event['Records']:
        for record in event['Records']:
            send_email(base64.b64decode(record['body']))
    return event
