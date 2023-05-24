import os

import boto3

sqs = boto3.client('sqs')

queue_url = os.environ.get('CHANGES_SQS_QUEUE_URL')


def lambda_handler(event, context):
    entries = [{
        'Id': record['kinesis']['sequenceNumber'],
        'MessageBody': record['kinesis']['data'],
        'MessageDeduplicationId': record['kinesis']['sequenceNumber'],
        'MessageGroupId': record['kinesis']['partitionKey']
    } for record in event['Records']]

    max_batch_size = 10  # current maximum allowed

    if entries:
        print("Sending data")
        chunks = [entries[x:x + max_batch_size] for x in range(0, len(entries), max_batch_size)]
        for chunk in chunks:
            sqs.send_message_batch(
                QueueUrl=queue_url,
                Entries=chunk
            )
    else:
        print("Nothing to send")

    return {
        'message': 'Completed'
    }
