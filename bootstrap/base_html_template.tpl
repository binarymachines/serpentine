<!DOCTYPE html>

<!-- paulirish.com/2008/conditional-stylesheets-vs-css-hacks-answer-neither/ -->
<!--[if lt IE 7]> <html class="no-js lt-ie9 lt-ie8 lt-ie7" lang="en"> <![endif]-->
<!--[if IE 7]>    <html class="no-js lt-ie9 lt-ie8" lang="en"> <![endif]-->
<!--[if IE 8]>    <html class="no-js lt-ie9" lang="en"> <![endif]-->
<!--[if gt IE 8]><!--> 
<html class="no-js" lang="en"> 
<!--<![endif]-->
<head>
	<meta charset="utf-8" />

	<!-- Set the viewport width to device width for mobile -->
	<meta name="viewport" content="width=device-width" />

	<title>
    {% raw %}
        {% block title %}
            Page Title 
        {% endblock %}
    {% endraw %}
    </title>
  
	<!-- Included CSS Files -->
	
	
	<link rel="stylesheet" href="/{{ config.url_base }}/static/styles/foundation.css"/>
	<link rel="stylesheet" href="/{{ config.url_base }}/static/styles/app.css"/>
	
    <link type="text/css" href="/{{ config.url_base }}/static/styles/jquery-ui-custom.css" rel="stylesheet" />
    <link type="text/css" href="/{{ config.url_base }}/static/styles/jquery-ui-mods.css" rel="stylesheet"/>

    <script type="text/javascript" src="/{{ config.url_base }}/static/scripts/jquery.min.js"></script>
    <script type="text/javascript" src="/{{ config.url_base }}/static/scripts/jquery-ui.js"></script>   
    
    <script type="text/javascript" src="/{{ config.url_base }}/static/scripts/foundation.js"></script>
    <script type="text/javascript" src="/{{ config.url_base }}/static/scripts/app.js"></script>

    <script type="text/javascript" src="/{{ config.url_base }}/static/scripts/jquery-ui-timepicker-addon.js"></script>
    <script type="text/javascript" src="/{{ config.url_base }}/static/scripts/serpentine.js"></script>
    <script type="text/javascript" src="/{{ config.url_base }}/static/scripts/table_select_logic.js"></script>

	<!--[if lt IE 9]>
		<link rel="stylesheet" href="stylesheets/ie.css">
	<![endif]-->
	
	<script src="/{{config.url_base}}/static/scripts/modernizr.foundation.js"></script>

	<!-- IE Fix for HTML5 Tags -->
	<!--[if lt IE 9]>
		<script src="http://html5shiv.googlecode.com/svn/trunk/html5.js"></script>
	<![endif]-->


    {% raw %}
    {% block user_scripts %}
        <!-- placeholder for user-defined javscript code blocks -->
    {% endblock %}
    {% endraw %}
</head>
<body>

	<!-- container -->
	<div class="container">

        <div class="row">
        &nbsp;
        </div>
		<div class="row">
		     <div class="twelve columns">
    			<div class="two columns">
    				<h2>{{ config.app_name }}</h2>	
                </div
                <div class="ten columns">
                    <br/>
                    <h5>version {{ config.app_version }}</h5>		
                </div>	
            </div>
        </div>
        <div class="row" id="header">
            <div class="twelve columns">
                {% raw %}
                {% block nav %}
				<ul class="nav-bar">
                	<li class="has-flyout">
                		<a href="#" class="main">Home</a>
                		<a href="#" class="flyout-toggle"><span></span></a>
                		<div class="flyout">
                			<ul>
                                <li><a href="#">Login</a></li>                                                                                        
                                <li><a href="#">Logout</a></li>
                                <li><a href="#">Dashboard</a></li>
                                <li><a href="#"><hr/></a></li>
                                <li><a href="#">Preferences</a></li>
                			</ul>
                		</div>
                    </li>                	
                	<li class="has-flyout">
                		<a href="#" class="main">Navitem 2</a>                		
                	</li>
                	<li class="has-flyout">
                		<a href="#" class="main">Navitem 3</a>                		
                	</li>
                	<li class="has-flyout">
                		<a href="#" class="main">Navitem 4</a>                		
                	</li>                	
                	<li><input type="search" /></li>
                </ul>
                {% endblock %}
                {% endraw %}
			</div> 
         </div> <!-- end header div -->
		
		
		

		<div class="row">
			<div class="twelve columns">
                <div class="panel">
                {% raw %}
                {% block content_header %}
                    <h5>Page Title</h>
                    <p>page subtitle</p>
                {% endblock %}
                {% endraw %}
                </div>
				{% raw %}				
				{% block content %}
				
				
				{% endblock %}
				{% endraw %}
                
				
			</div>
        </div>
			
	</div>
	<!-- container -->



</body>
</html>
