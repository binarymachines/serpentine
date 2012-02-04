#!/bin/bash


# installs the generated code and content into the Serpentine app directories

cp *.html ../templates/
cp -R styles ../templates/
cp -R scripts ../templates/
cp *.py ..
cp *.conf ..
cp *.wsgi ..