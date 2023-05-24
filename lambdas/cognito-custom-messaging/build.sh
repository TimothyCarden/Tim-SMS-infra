#!/usr/bin/env sh

pip3 install --target ./package -r requirements.txt
cd package || exit
zip -r ../cognito-custom-messaging-package.zip .
cd ../
zip -g cognito-custom-messaging-package.zip lambda_function.py templates/*
rm -R ./package
