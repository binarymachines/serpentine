# 
# YAML Serpentine config file (generated from template).
# This is used by the Serpentine configuration script to generate a starting config.
#

global:
        app_name:                       {{ config.app_name }}
        app_version:                    1.0
        app_root:                       {{ config.app_root }}        
        static_file_directory:          {{ config.static_file_directory }}
        output_file_directory:          output
        report_file_directory:          reports
        xsl_stylesheet_directory:       {{ config.xsl_stylesheet_directory }}
        default_form_package:           {{ config.default_form_package }}
        default_model_package:          {{ config.default_model_package }}
        default_helper_package:         {{ config.default_helper_package }}
        default_controller_package:     {{ config.default_controller_package }} 
        default_responder_package:      {{ config.default_responder_package }}
        default_datasource_package:     {{ config.default_datasource_package }}
        default_report_package:         {{ config.default_reporting_package }}
	default_plugin_package:		{{ config.default_plugin_package }}
        startup_db:                     {{ config.startup_db }}
        url_base:                       {{ config.url_base }}
        security_posture:               open
        login_template:                 login.html
        
# experimental support for self-documenting features
        api_frame:                      api.html
        doc_frame:                      doc.html
        config_frame:                   config.html
        controller_frame:               controller_frame.html        
        #model_frame:                   model_frame.html
        responder_frame:                responder_frame.html
        # control_frame:                control_frame.html
        # datasource_frame:             datasource_frame.html
        #helper_frame:                  helper_frame.html



security_registry:
    secured_object_groups:
            frames_default:
                    object_type:            frame
                    members:                ()
                    permissions:
                                            - action: render                                         
                                              access: allow(&users), deny(&guests)                         
                    denial_redirect_route:  frame/login
                                        
            methods_default:
                    object_type:            method
                    members:                () 
                    permissions:
                                            - action: call
                                              access: allow(&users), deny(&guests)
                    denial_redirect_route:  frame/deny 



plugins:
{% for plugin_alias in config.plugins %}	
	{{ plugin_alias }}:
		class: {{ config.plugins[plugin_alias].class_name }}
		slots:
		{% for slot in config.plugins[plugin_alias].slots %}
			- method:	{{ slot.method }}
			  route:  	{{ slot.route_extension }}
			  request_type:	{{ slot.request_type }}
	        {% endfor %}
{% endfor %}


#        
# Each entry in the content registry under 'frames' is a frame ID.
# The 'type' is either html or xml; specification is optional, it's only
# consulted if the registry can't guess the type from the filename.
#
content_registry:
    template_directory: {{ config.template_directory }}
    frames:
            home:
                   template:    main.html
        {% for frame in config.frames %}
            {{ config.frames[frame].name }}:
                   template:   {{ config.frames[frame].template }}
                   form:       {{ config.frames[frame].form }}
                   type:       {{ config.frames[frame].type }}
        {% endfor %}


#
# Datasources for populating UI controls. 
# Each datasource has a name and an arbitrary set of parameters.
#
datasources:
        {% for source in config.datasources %}
        {{ source }}:
            type:           {{ config.datasources[source].type }}   
            {% for param in config.datasources[source].params %}
            {{ param.name }}:       {{ param.value }}{% endfor %}
        {% endfor %}   
            

#
# UI control objects, rendered via templates (frames in the content registry).
# Controls are dynamic, receiving their data from named datasources.
#
ui-controls:
        {% for controlName in config.controls %}
        {{ controlName }}:
            type:        {{ config.controls[controlName].type }}            
            datasource:  {{ config.controls[controlName].datasource }}            
            template:    {{ config.controls[controlName].template }}      # optional; only need to specify for custom controls
        {% endfor %}

#
# Each entry in the models section represents the mapping between a Model and its
# database table.  The optional "children" entry under each model consists of 1 to N model names
# separated by a comma.
#
models:
        {% for model in config.models %}
        {{ config.models[model].name }}:
              table:      {{ config.models[model].table }}
              children:   {{ config.models[model].children }}

        {% endfor %}

#
# Each entry in the controllers section is the class name of a controller
# (relative to the package name specified in the global setting 'default_controller_package')
# followed by its alias, model class, and form class.
#
# The default package resolution behavior is overridden by specifying a fully qualified package name
# for the controller, i.e. my.package.ControllerClass.
#
# A controller's alias is expected to match the unqualified class name of the Model it controls;
# the entry WidgetController: Widget sets the controller's alias *and* links it to the 
# <default_dbtypes_package>.Widget class. To override this behavior, specify the target classname
# in the optional "model" attribute.
#
#
controllers:
        {% for controller in config.controllers %}
        {{ config.controllers[controller].name }}:
            alias:      {{ config.controllers[controller].alias }}
            model:      {{ config.controllers[controller].model }}

        {% endfor %}


# TODO: alter program logic so that the ViewManager will infer the proper frame
# from the name of the controller and method.
view_manager:
        controllers:  
            {% for controller in config.controllers %}
            {{ config.controllers[controller].alias }}:
                {% for method in config.controllers[controller].methods %}
                - method:       {{ method.name }}
                  frame:        {{ method.frame }}                
                {% endfor %}
            {% endfor %}
 
# TODO: update ReportSpec to populate this section
reports:
        


# Each entry under the frames: heading is a frame alias (previously registered with the 
# ContentManager) with a corresponding reference to an XSL stylesheet. The referenced frame
# should be of type XMLFrame.
# TODO: alter the program logic so that by default we don't need any entries here;
# DisplayManager will auto-guess the stylesheet name based on the frame's name.
# Serpentine will look for stylesheets in the location specified by the global setting
# xsl_stylesheet_directory (relative to the app_root directory).

display_manager:
        frames:    
            {% for frame in config.xmlFrames %}
            {{ frame }}:
                stylesheet:     {{ config.getStylesheet(frame) }} 
            {% endfor %}



# We can configure multiple databases. Each named database will result
# in the creation of a PersistenceManager instance.
# At application startup, the Environment object with contain
# the PersistenceManager designated in the global setting
# 'startup_db'.
databases:   
        
        {% for db in config.databases %}
        {{ db }}:
            type:           {{ config.databases[db].type }}
            host:           {{ config.databases[db].host }}
            schema:         {{ config.databases[db].schema }}
            username:       {{ config.databases[db].username }}
            password:       {{ config.databases[db].password }}
        {% endfor %}                         



                        
