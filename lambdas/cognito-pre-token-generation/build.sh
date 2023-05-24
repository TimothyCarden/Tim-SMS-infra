#!/usr/bin/env sh

pip3 install --target ./package -r requirements.txt
cd package || exit
zip -r ../cognito-pre-token-generation-package.zip .
cd ../
zip -g cognito-pre-token-generation-package.zip lambda_function.py
rm -R ./package