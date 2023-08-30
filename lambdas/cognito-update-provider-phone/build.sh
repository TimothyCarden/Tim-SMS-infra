#!/usr/bin/env sh

pip3 install --target ./package -r requirements.txt
cd package || exit
zip -r ../cognito-update-provider-phone.zip .
cd ../
zip -g cognito-update-provider-phone.zip lambda_function.py
rm -R ./package