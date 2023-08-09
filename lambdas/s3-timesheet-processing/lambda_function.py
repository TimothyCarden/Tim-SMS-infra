import json
import logging
import os
import sys
import tempfile
from io import BytesIO
from urllib.parse import unquote_plus

import boto3
import psycopg2
from PIL import Image, ImageOps
from botocore.exceptions import ClientError
from pdf2image import convert_from_bytes

logger = logging.getLogger()
logger.setLevel(logging.INFO)

region_name = os.environ['AWS_REGION']

session = boto3.session.Session()
client = session.client(
    service_name='secretsmanager',
    region_name=region_name,
)

s3_client = boto3.client('s3')

size = 1024, 1024

image_extensions = ['png', 'jpeg', 'jpg']
pdf_extensions = ['pdf']
valid_extensions = ['txt'] + image_extensions + pdf_extensions


def get_secret(secret_name):
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as err:
        if err.response['Error']['Code'] == 'ResourceNotFoundException':
            print("The requested secret " + secret_name + " was not found")
        elif err.response['Error']['Code'] == 'InvalidRequestException':
            print("The request was invalid due to:", err)
        elif err.response['Error']['Code'] == 'InvalidParameterException':
            print("The request had invalid params:", err)
        elif err.response['Error']['Code'] == 'DecryptionFailure':
            print("The requested secret can't be decrypted using the provided KMS key:", err)
        elif err.response['Error']['Code'] == 'InternalServiceError':
            print("An error occurred on service side:", err)
    else:
        # Secrets Manager decrypts the secret value using the associated KMS CMK
        # Depending on whether the secret was a string or binary, only one of these fields will be populated
        if 'SecretString' in get_secret_value_response:
            return get_secret_value_response['SecretString']
        else:
            return get_secret_value_response['SecretBinary']


# rds settings
jdbc_url = get_secret(os.environ['DB_URL'])
username = get_secret(os.environ['DB_USERNAME'])
password = get_secret(os.environ['DB_PASSWORD'])


def get_connection():
    try:
        logger.info("getting connection from db")
        connect = psycopg2.connect(dsn=jdbc_url[5:jdbc_url.index('?')], user=username, password=password,
                                   connect_timeout=5)
        logger.info("SUCCESS: Connection to RDS PostgreSQL instance succeeded")
        return connect
    except psycopg2.Error as e:
        logger.error("ERROR: Unexpected error: Could not connect to PostgreSQL instance.")
        logger.error(e)
        sys.exit()


def resize_image(image_path, file_extension):
    buffer = BytesIO()
    try:
        with Image.open(image_path) as image:
            image = ImageOps.exif_transpose(image)
            image.thumbnail(size)
            try:
                if file_extension == 'jpg':
                    file_extension = 'jpeg'
                image.save(buffer, format=file_extension)
                return buffer
            except Exception as e:
                type, value, traceback = sys.exc_info()
                logger.error('Error saving thumbnail %s: %s' % (value.filename, value.strerror))
                logger.error(e)
                return None
    except Exception as e:
        logger.error("Failed to open image")
        logger.error(e)
        return None


def process_s3_event(json_str):
    conn = None
    try:
        logger.info(json_str)
        events = json.loads(json_str)
        if 'Records' in events:
            for event in events['Records']:
                if 's3' in event:
                    bucket_name = event['s3']['bucket']['name']
                    object_key = unquote_plus(event['s3']['object']['key'])
                    logger.info(f'bucket: {bucket_name} object: {object_key}')
                    conn = get_connection()
                    cur = conn.cursor()
                    if 'timesheets' in object_key:
                        process_timesheet(bucket_name, object_key, cur)
                    if 'credentials' in object_key:
                        process_credentials(bucket_name, object_key, cur)
                    conn.commit()
                    cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        raise error
    finally:
        if conn is not None:
            conn.close()


def process_timesheet(bucket_name, object_key, cur):
    for path in object_key.split('/'):
        if path.startswith('shift='):
            shift_id = path.split('=')[1]
            logger.info(f'shift {shift_id}')
            obj, file_extension = get_object(bucket_name, object_key)
            if obj and file_extension:
                thumbnail_link, thumbnail_extension = make_thumbnail(bucket_name, object_key, obj)
                sql = """update workforce.shift_order_time_sheet 
                            set file_url = %s, 
                                file_type = %s,
                                thumbnail_file_url = %s,
                                thumbnail_type = %s,
                                upload_datetime = now() 
                          where shift_order_id = %s RETURNING id;"""
                cur.execute(sql, (object_key, file_extension, thumbnail_link, thumbnail_extension, shift_id))
                id = cur.fetchone()[0]
                logger.info(f"updated id = {id}")
            else:
                logger.warning(f"Nothing to update: obj is {bucket_name}, file_extension is {file_extension}")


def process_credentials(bucket_name, object_key, cur):
    object_type = None
    for path in object_key.split('/'):
        if path.startswith('licenses'):
            object_type = 'license'
        if path.startswith('certifications'):
            object_type = 'certification'
        if path.endswith('.original'):
            id = path.split('.')[0]
            logger.info(f'{object_type}Id={id}')
            obj, file_extension = get_object(bucket_name, object_key)
            thumbnail_link, thumbnail_extension = make_thumbnail(bucket_name, object_key, obj)
            sql = f"""update workforce.provider_credentials_{object_type} 
                         set file_link = %s, 
                             file_type = %s,
                             thumbnail_file_link = %s,
                             thumbnail_type = %s 
                       where id = %s RETURNING id;"""
            cur.execute(sql, (object_key, file_extension, thumbnail_link, thumbnail_extension, id))
            record = cur.fetchone()
            if record and record[0]:
                id = record[0]
                logger.info(f"updated id = {id}")
            else:
                logger.error(f"Couldn't update {object_key} with id {id}. Reason - not found")


def get_file_extension(obj_key, obj):
    if obj.get('ContentType') not in ['application/octet-stream', 'binary/octet-stream']:
        return obj.get('ContentType').split('/')[1]

    _, tail = os.path.split(obj_key)
    elements = tail.split('.')
    if len(elements) > 2:
        extension = elements[len(elements) - 2]
        if extension in valid_extensions:
            return extension
    return None


def pdf_to_image(pdf_file_bytes):
    with tempfile.TemporaryDirectory() as path:
        images = convert_from_bytes(
            pdf_file_bytes,
            first_page=1,
            last_page=1,
            dpi=300,
            fmt='jpeg',
            size=size,
            thread_count=8,
            output_folder=path,
            jpegopt={"quality": 100, "optimize": False, "progressive": False}
        )
        size_images = len(images)
        logger.info(f"Image are ready")
        if size_images > 0:
            buffer = BytesIO()
            images[0].save(buffer, 'jpeg'.upper())
            return buffer
        return None


def upload_to_s3(bucket_name, head, tail, buffer):
    logger.info('thumbnail uploading')
    buffer.seek(0)
    obj_key = '{}/{}'.format(
        head,
        tail.replace('.original', '.thumbnail')
    )
    s3_client.upload_fileobj(buffer, bucket_name, obj_key)
    logger.info("thumbnail uploaded")
    return obj_key


def get_object(bucket_name, object_key):
    logger.info(f'downloading image {object_key}')
    obj = s3_client.get_object(
        Bucket=bucket_name, Key=object_key
    )
    logger.info(f'object: {obj}')
    if not obj.get('ContentLength') or obj.get('ContentLength') == 0:
        logger.info(f"File {object_key} has 0 size")
        return None, None
    file_extension = get_file_extension(object_key, obj)
    return obj, file_extension


def make_thumbnail(bucket_name, object_key, obj):
    file_extension = get_file_extension(object_key, obj)
    logger.info(f"extension {file_extension}")
    head, tail = os.path.split(object_key)

    if file_extension not in valid_extensions:
        logger.error(f"File extension {file_extension} is not valid")
        return None

    if file_extension in image_extensions:
        logger.info('resizing image')
        buffer = resize_image(BytesIO(obj['Body'].read()), file_extension)
        uploaded_key = upload_to_s3(bucket_name, head, tail, buffer)
        return uploaded_key, file_extension

    if file_extension in pdf_extensions:
        logger.info("PDF to image")
        buffer = pdf_to_image(bytes(obj['Body'].read()))
        if buffer:
            uploaded_key = upload_to_s3(bucket_name, head,
                                        tail.replace(f'.{file_extension}.original', '.jpeg.original'), buffer
                                        )
            return uploaded_key, "jpeg"
        else:
            logger.error("Failed to process pdf to image")
            return None


def lambda_handler(event, context):
    logger.info(event)
    if event['Records']:
        for record in event['Records']:
            process_s3_event(record['body'])
    return event
