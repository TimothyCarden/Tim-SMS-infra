#!/usr/bin/env sh

pip3 install --platform manylinux2014_x86_64 --target=package --implementation cp --python 3.9 --only-binary=:all: --upgrade pillow

pip3 install --target ./package -r requirements.txt
cd package || exit
zip -r ../s3-timesheet-processing-package.zip .
cd ../
zip -g s3-timesheet-processing-package.zip lambda_function.py
rm -R ./package
