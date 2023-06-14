#!/usr/bin/env sh

pip3 install --target ./package -r requirements.txt
cd package || exit
zip -r ../cognito-import-providers-package.zip .
cd ../
zip -g cognito-import-providers-package.zip lambda_function.py
rm -R ./package