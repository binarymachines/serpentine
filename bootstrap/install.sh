#!/bin/bash


# installs the generated code and content into the Serpentine app directories

cp *.html ../templates/
cp -R js ../templates/
cp -R css ../templates/
cp -R fonts ../templates/
cp -R images ../templates/
cp radio_group_control.tpl select_control.tpl table.tpl table_multiselect.tpl ../templates/
cp *.py ..
cp *.conf ..
cp *.wsgi ..