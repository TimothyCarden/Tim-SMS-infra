from __future__ import absolute_import, print_function

import posixpath as path
from gzip import GzipFile
from io import BytesIO

import boto3
from botocore.exceptions import ClientError
from jinja2 import BaseLoader, TemplateNotFound


def gzip(content, filename=None, compresslevel=9):
    gzbuffer = BytesIO()
    gz = GzipFile(filename, 'wb', compresslevel, gzbuffer)
    gz.write(content)
    gz.close()
    return gzbuffer.getvalue()


def gunzip(gzcontent):
    gzbuffer = BytesIO(gzcontent)
    return GzipFile(None, 'rb', fileobj=gzbuffer).read()


class S3loader(BaseLoader):

    def __init__(self, bucket, prefix='', s3=None):
        self.bucket = bucket
        self.prefix = prefix
        self.s3 = s3 or boto3.client('s3')
        super(S3loader, self).__init__()

    def get_source(self, environment, template):
        if self.prefix:
            template = path.join(self.prefix, template)
        try:
            resp = self.s3.get_object(Bucket=self.bucket, Key=template)
        except ClientError as e:
            if "NoSuchKey" in e.__str__():
                raise TemplateNotFound(template)
            else:
                raise e
        if 'ContentEncoding' in resp and 'gzip' in resp['ContentEncoding']:
            body = gunzip(resp['Body'].read())
        else:
            body = resp['Body'].read()
        return body.decode('utf-8'), None, lambda: True
