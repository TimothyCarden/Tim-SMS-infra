import logging
import os
import secrets
import string

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

otp_length = int(os.environ.get("OTP_LENGTH"))
exclude_numbers = os.environ.get("BY_PASS_PHONE_NUMBERS").split(",")
send_sms = os.environ.get("NEED_SEND_SMS")

client = boto3.client('sns')


def lambda_handler(event, context):
    logger.info("CUSTOM_CHALLENGE_LAMBDA: %s", event['request'])
    alphabet = string.digits

    phone_number = event['request']['userAttributes']['phone_number']

    if phone_number in exclude_numbers or send_sms == "0":
        otp = '111111'
    else:
        otp = ''.join(secrets.choice(alphabet) for _ in range(otp_length))
        client.publish(
            Message=f'{otp} is your verification code for Actriv',
            PhoneNumber=phone_number
        )

    client.publish(
        Message=f'{otp} is your verification code for Actriv',
        PhoneNumber=event['request']['userAttributes']['phone_number']
    )

    event['response']['privateChallengeParameters'] = dict()
    event['response']['privateChallengeParameters']['otp'] = otp
    return event

