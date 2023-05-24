#!/usr/bin/env sh

pip3 install --target ./package -r requirements.txt
cd package || exit
zip -r ../email-service-package.zip .
cd ../
zip -g email-service-package.zip lambda_function.py s3_template_loader.py
rm -R ./package
