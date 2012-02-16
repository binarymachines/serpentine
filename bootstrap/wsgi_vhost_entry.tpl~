<VirtualHost {{ config.hostname }}:{{ config.port }}>
    DocumentRoot "{{ config.app_root }}"
    ServerName {{ config.hostname }}   
 
    WSGIDaemonProcess test user=dtaylor group=admin processes=1 threads=5
    WSGIScriptAlias /{{ config.web_app_name }}     {{ config.app_root }}/{{ config.web_app_name }}.wsgi
    <Directory {{ config.app_root }}>
               WSGIProcessGroup {{ config.web_app_name }}
               WSGIApplicationGroup %{GLOBAL}
               Order deny,allow
               Allow from all
    </Directory>
</VirtualHost>
