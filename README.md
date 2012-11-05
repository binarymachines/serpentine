Serpentine
==========

A new Python web application stack.


Single point of configuration (YAML config file). Create a view like this:

````
content_registry:
    template_directory:     templates
    frames:
            widget_index:
                            mywidgetlist.html
````

Register a controller like this:
(the model classes are generated automatically from your database schema)

````
controllers:
    WidgetController:       
            alias:          Widget
            model:          Widget
````

Marry a view to a controller method like this:

````
view_manager:
    controllers:
            Widget:
                - method:   index       # list all widgets in the DB
                  frame:    widget_index
````

And then you can invoke your controller method like this:


http://localhost:port/serpentine/controller/Widget


Need data-driven, dynamic controls in your web pages?
Specify a control (on the server side) like this:

````
ui-controls:
    widget_style_selector:
            type:           select
            datasource:     widget_styles_src
````

Make sure there's a matching datasource, like this:

````
datasources:
    widget_styles_src:
            type:           menu
            table:          lookup_widget_styles  # this table must exist in your schema
````

And then in your client-side javascript you can render say
(if you reference serpentine.js):

````javascript
renderControl("MyWidgetApp, "widget_style_selector", "target_div");
````

to render an HTML dropdown control within the target div, where the options in the dropdown
are provided by the server-side datasource.





















