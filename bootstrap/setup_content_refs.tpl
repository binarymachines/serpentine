#!/bin/bash


cd ../{{ config.static_file_directory }}/styles
ln -s smoothness/jquery-ui-1.8.16.custom.css jquery-ui-custom.css
cd -
cd ../{{ config.static_file_directory }}/scripts
ln -s jquery-1.6.2.js jquery.js
ln -s jquery-ui-1.8.16.custom.min.js jquery-ui.js