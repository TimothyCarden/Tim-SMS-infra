#!/usr/bin/env sh

pip3 install --target ./package -r requirements.txt
cd package || exit
zip -r ../cognito-post-auth-package.zip .
cd ../
zip -g cognito-post-auth-package.zip lambda_function.py
rm -R ./package