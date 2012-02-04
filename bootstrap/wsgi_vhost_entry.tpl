<VirtualHost {{ hostname }}:{{ port }}>
    DocumentRoot "{{ app_root }}"
    ServerName {{ hostname }}   
 
    WSGIDaemonProcess test user=dtaylor group=admin processes=1 threads=5
    WSGIScriptAlias /{{ web_app_name }}     {{ app_root }}/{{ web_app_name }}.wsgi
    <Directory {{ app_root }}>
               WSGIProcessGroup {{ web_app_name }}
               WSGIApplicationGroup %{GLOBAL}
               Order deny,allow
               Allow from all
    </Directory>
</VirtualHost>
