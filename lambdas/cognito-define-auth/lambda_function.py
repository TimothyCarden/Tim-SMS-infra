import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    request = event['request']
    logger.info(request)

    response = event['response']
    user_not_found = request.get('userNotFound')
    # If user is not registered
    if user_not_found:
        response['issueTokens'] = False
        response['failAuthentication'] = True
        return event

    session = request['session']

    if len(session) > 3 and not session[-1]['challengeResult']:
        response['issueTokens'] = False
        response['failAuthentication'] = True
        return event

    if len(session) > 0 and session[-1]['challengeResult']:
        response['issueTokens'] = True
        response['failAuthentication'] = False
        return event

    response['issueTokens'] = False
    response['failAuthentication'] = False
    response['challengeName'] = 'CUSTOM_CHALLENGE'

    return event
