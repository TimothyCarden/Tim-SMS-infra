#!/usr/bin/env sh

pip3 install --target ./package -r requirements.txt
cd package || exit
zip -r ../embedding-quicksight-api-package.zip .
cd ../
zip -g embedding-quicksight-api-package.zip lambda_function.py
rm -R ./package