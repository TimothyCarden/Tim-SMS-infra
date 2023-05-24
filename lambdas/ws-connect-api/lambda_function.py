import datetime
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

table_name_facilities = os.environ['DD_TABLE_NAME_FACILITIES']
table_name_providers = os.environ['DD_TABLE_NAME_PROVIDERS']


def get_ttl():
    return int((datetime.datetime.now() + datetime.timedelta(days=1)).timestamp())


def handle_connect(second_id, table, connection_id, column):
    status_code = 200
    try:
        table.put_item(
            Item={'connection_id': connection_id, column: second_id, 'ttl': get_ttl()})
        logger.info(
            f"Added connection %s for {column} %s.", connection_id, second_id)
    except ClientError:
        logger.exception(
            f"Couldn't add connection %s for {column} %s.", connection_id, second_id)
        status_code = 503
    return status_code


def handle_disconnect(table_facilities, table_providers, connection_id):
    status_code = 200
    try:
        table_facilities.delete_item(Key={'connection_id': connection_id})
        table_providers.delete_item(Key={'connection_id': connection_id})
        logger.info("Disconnected connection %s.", connection_id)
    except ClientError:
        logger.exception("Couldn't disconnect connection %s.", connection_id)
        status_code = 503
    return status_code


def lambda_handler(event, context):
    route_key = event.get('requestContext', {}).get('routeKey')
    connection_id = event.get('requestContext', {}).get('connectionId')
    if table_name_facilities is None or table_name_providers is None or route_key is None or connection_id is None:
        return {'statusCode': 400}
    table_facilities = boto3.resource('dynamodb').Table(table_name_facilities)
    table_providers = boto3.resource('dynamodb').Table(table_name_providers)
    logger.info("Request: %s, use table %s.", route_key, table_facilities.name)
    response = {'statusCode': 200}
    if route_key == '$connect':
        facility_id = event.get('queryStringParameters').get('facility_id')
        provider_id = event.get('queryStringParameters').get('provider_id')
        if provider_id is None:
            response['statusCode'] = handle_connect(facility_id, table_facilities, connection_id, 'facility_id')
        elif facility_id is None:
            response['statusCode'] = handle_connect(provider_id, table_providers, connection_id, 'provider_id')
        else:
            response['statusCode'] = 400
    elif route_key == '$disconnect':
        response['statusCode'] = handle_disconnect(table_facilities, table_providers, connection_id)
    elif route_key == 'ping':
        response['statusCode'] = 200
        response['body'] = 'pong'
    else:
        response['statusCode'] = 404

    return response
