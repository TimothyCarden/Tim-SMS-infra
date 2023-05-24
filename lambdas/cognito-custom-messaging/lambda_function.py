import logging
import os

from jinja2 import FileSystemLoader, Environment, select_autoescape

logger = logging.getLogger()
logger.setLevel(logging.INFO)

domain = os.environ['APP_DOMAIN']

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape()
)


def confirm_sign_up(request):
    username = request.get('usernameParameter')
    code = request.get('codeParameter')
    template = env.get_template('confirm_sign_up.html')
    output = template.render({
        'email_title': 'Signup Confirmation',
        'user_name': username,
        'actrusfm_url': domain,
        'verification_code': code
    })
    return {
        'emailSubject': 'Signup Confirmation',
        'emailMessage': output
    }


def recover_password(request):
    email = request.get('userAttributes').get('email')
    code = request.get('codeParameter')
    template = env.get_template('recover_password.html')
    output = template.render({
        'user_name': email,
        'reset_link': f'{domain}/auth/reset-password?email={email}&code={code}'
    })
    return {
        'emailSubject': 'Password Recovery',
        'emailMessage': output
    }


def lambda_handler(event, context):
    logger.info(event)
    if event.get('request').get('userAttributes') is None:
        return event

    if event.get('triggerSource') == "CustomMessage_AdminCreateUser":
        event['response'] = confirm_sign_up(event.get('request'))

    if event.get('triggerSource') == "CustomMessage_ForgotPassword":
        event['response'] = recover_password(event.get('request'))
    return event
