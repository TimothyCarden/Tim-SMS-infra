#!/usr/bin/env sh

pip3 install --target ./package -r requirements.txt
cd package || exit
zip -r ../manage-providers-package.zip .
cd ../
zip -g manage-providers-package.zip lambda_function.py
rm -R ./package
