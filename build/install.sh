#!/bin/bash


# installs the generated code and content into the Serpentine app directories

cp *.html ../deploy/templates/
cp -R styles ../deploy/templates/
cp -R scripts ../deploy/templates/
cp -R images ../deploy/templates/
cp radio_group_control.tpl select_control.tpl table.tpl table_multiselect.tpl ../deploy/templates/
cp *.py ../deploy
cp *.conf ../deploy
cp *.wsgi ../deploy