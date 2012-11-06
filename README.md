Serpentine
==========

A new Python web application stack built on top of the bottle web framework. 
It's MVC, database-forward, tweak-friendly, AJAX- and JSON-aware.
It deals with complexity in an intelligent way -- while letting
simple things be simple. Build CRUD apps or RESTful API's quickly
and reusably.


* Single point of configuration (YAML config file). Create a view like this:

````yaml
content_registry:
    template_directory:     templates
    frames:
            widget_index:
                            mywidgetlist.html
````

Register a controller like this:
(the model and controller classes are generated automatically from your database schema, 
or you can write your own)

````yaml
controllers:
    WidgetController:       
            alias:          Widget
            model:          Widget
````

Marry a view to a controller method like this:

````yaml
view_manager:
    controllers:
            Widget:
                - method:   index       # list all widgets in the DB
                  frame:    widget_index
````

And then you can invoke your controller method like this:


http://localhost:port/serpentine/controller/Widget

* Serpentine makes it easy to do the things you end up having to do all the time
when writing web apps. For example: need data-driven, dynamic controls in your forms
--such as dropdowns to populate fields with constrained values?
Specify a control (on the server side) in your init file, like this:

````yaml
ui-controls:
    widget_style_selector:
            type:           select
            datasource:     widget_styles_src
````

Make sure there's a matching datasource, like this:

````yaml
datasources:
    widget_styles_src:
            type:           menu
            table:          lookup_widget_styles  # this table must exist in your schema
````

And then in your client-side javascript you can render say
(once you reference serpentine.js):

````javascript
renderControl("MyWidgetApp", "widget_style_selector", "target_div");
````

to render an HTML dropdown control within the target div, where the options in the dropdown
are provided by the server-side datasource.


But wait, there's more! 

Want to return a custom JSON object to a client-side Javascript component?
Subclass Responder:

````python
class MyCustomResponder(Responder):
    def respond(httpRequest, context, **kwargs):
        result = {}
        # load up the result dictionary with arbitrary data,
        # whether from the database or another source
        return result
````

register the responder in the Serpentine init file:


````yaml
responders:
        MyCustomResponder:
            alias:          myresp
            type:           json
````


and then invoke it via URL:

````
http://localhost:port/serpentine/responder/myresp
````




        
        





















