<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=ASCII" />
    <title>
        {% block title %}
            Page Title 
        {% endblock %}
    </title>
    
    <link rel="stylesheet" href="/samplespace/static/styles/main.css" type="text/css" media="screen,projection" />
    <link type="text/css" href="/samplespace/static/styles/smoothness/jquery-ui-custom.css" rel="stylesheet" />
    <link type="text/css" href="/samplespace/static/styles/jquery-ui-mods.css" rel="stylesheet"/>
    
    <script type="text/javascript" src="/samplespace/static/scripts/jquery.js"></script>
    <script type="text/javascript" src="/samplespace/static/scripts/jquery-ui.js"></script>
    <script src="/samplespace/static/scripts/jquery-ui-timepicker-addon.js" language="javascript"></script>
    <script src="/samplespace/static/scripts/tablestripes.js" language="javascript"></script>
    <script src="samplespace/static/scripts/serpentine.js" language="javascript"></script>
    
        
    {% block user_scripts %}
        <!-- placeholder for user-defined javscript code blocks -->
    {% endblock %}
    
  </head>
  <body>
    <div id="wrapper">
        <div id="innerwrapper">

            <div id="header">
    		      <h1><a href="#">{{ app_name }}</a></h1>
    				
    				<h2>				
    				v{{ app_version }} {% block nav_breadcrumb %}{% endblock %}
    				</h2>
    				{% block nav %}
    				<ul id="nav">
    				
    						<li><a href="#">Home</a></li>
    						
    						<li><a href="#">Nav Item 1</a></li>
    						
    						<li><a href="#">Nav Item 2</a></li>
    						
    						<li><a href="#">Nav Item 3</a></li>
    												
    				</ul>
    		        {% endblock %}
		      </div> <!-- end header div -->
		      
                {% block content_header %}
                
                {% endblock %}
                <div id="content">
                {% block content %}
    				
    		    {% endblock %}
    		    </div>
        </div> <!-- end innerwrapper div -->
    </div> <!-- end wrapper div -->
     
    <div id="footer">

    </div>
  </body>
</html>