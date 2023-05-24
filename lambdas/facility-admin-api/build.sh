#!/usr/bin/env sh

pip3 install --target ./package -r requirements.txt
cd package || exit
zip -r ../facility-admin-api-package.zip .
cd ../
zip -g facility-admin-api-package.zip lambda_function.py
rm -R ./package
