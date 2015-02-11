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
    
        {% block title %}
            {{ config.app_name }} Error Page
        {% endblock %}
    
    </title>
  
	<!-- Included CSS Files -->
	
	
	<link rel="stylesheet" href="/{{ config.url_base }}/static/styles/foundation.css"/>
	<link rel="stylesheet" href="/{{ config.url_base }}/static/styles/app.css"/>
	<!-- <link rel="stylesheet" href="/{{ config.url_base }}/static/styles/general_foundicons.css"/> -->
	
	
	<link href="/{{ config.url_base }}/static/styles/general_foundicons.css" media="screen" rel="stylesheet" type="text/css" />
    
    
    <!--[if lt IE 8]>
    <link href="/{{ config.url_base }}/static/styles/general_foundicons_ie7.css?1350599811" media="screen" rel="stylesheet" type="text/css" />
    <link href="/{{ config.url_base }}/static/styles/general_enclosed_foundicons_ie7.css?1350599811" media="screen" rel="stylesheet" type="text/css" />
    <link href="/{{ config.url_base }}/static/styles/social_foundicons_ie7.css?1350599811" media="screen" rel="stylesheet" type="text/css" />
    <link href="/{{ config.url_base }}/static/styles/accessibility_foundicons_ie7.css?1350599811" media="screen" rel="stylesheet" type="text/css" />
    <![endif]-->

	
	
	
    <link type="text/css" href="/{{ config.url_base }}/static/styles/jquery-ui-custom.css" rel="stylesheet" />
    <link type="text/css" href="/{{ config.url_base }}/static/styles/jquery-ui-mods.css" rel="stylesheet"/>

    <script type="text/javascript" src="/{{ config.url_base }}/static/scripts/jquery.min.js"></script>
    <script type="text/javascript" src="/{{ config.url_base }}/static/scripts/jquery-ui.js"></script>   
    
    <script type="text/javascript" src="/{{ config.url_base }}/static/scripts/foundation.js"></script>
    <script type="text/javascript" src="/{{ config.url_base }}/static/scripts/app.js"></script>

    <script type="text/javascript" src="/{{ config.url_base }}/static/scripts/jquery-ui-timepicker-addon.js"></script>
    <script type="text/javascript" src="/{{ config.url_base }}/static/scripts/serpentine.js"></script>
    

	<!--[if lt IE 9]>
		<link rel="stylesheet" href="stylesheets/ie.css">
	<![endif]-->
	
	<script src="/{{ config.url_base }}/static/scripts/modernizr.foundation.js"></script>

	<!-- IE Fix for HTML5 Tags -->
	<!--[if lt IE 9]>
		<script src="http://html5shiv.googlecode.com/svn/trunk/html5.js"></script>
	<![endif]-->


    
    {% block user_scripts %}
        <!-- placeholder for user-defined javscript code blocks -->
    {% endblock %}
    
</head>
<body>
<!-- Header and Nav -->
  
  <div class="row">
    <div class="twelve columns">
      <div class="panel">
        <h3>Error.</h3>
        <p>{{ config.app_name }} error handler page</p>
      </div>
    </div>
  </div>
  
  <!-- End Header and Nav -->
  
  
  <div class="row" style="margin-top: 100px; margin-bottom: 100px">    
    
    <!-- Main Feed -->
    <!-- This has been source ordered to come first in the markup (and on small devices) but to be to the right of the nav on larger screens -->
    <div class="eight columns">
      
      <!-- Feed Entry -->
      <div class="row">
        <div class="one column"><i class="foundicon-remove" style="font-size:28pt; color:red"></i></div>
        <div class="eleven columns">
          <h6><strong>Exception: {% raw %}{{exception.__class__.__name__}}{% endraw %}.</strong></h6>
          ({% raw %}{{exception.message}}{% endraw %})</p>
          <!--
          <ul class="link-list">
            <li><a href="">Reply</a></li>
            <li><a href="">Share</a></li>
          </ul>
          -->
          
          <h6><strong>Stacktrace:</strong></h6>
          {% raw %}
          {% for entry in stacktrace %}
          <div class="row">            
            <div class="twelve columns">
                <p>File: {{ entry[0] }}, line {{ entry[1] }} <br/>Function: {{ entry[2] }}(...)</p>
            </div>            
          </div>
          {% endfor %}
          {% endraw %}
        </div>
      </div>
      
    </div>
  </div>
    
  
  <!-- Footer -->
  
  <footer class="row">
    <div class="twelve columns">
      <hr />
      <div class="row">
        <div class="six columns">
          <p>The Serpentine open-source Python stack. New from Binary Machines. HTTP request handling by bottle. Forms by WTForms. Templates by Jinja2. ORM by SQLAlchemy. HTML/CSS by Foundation. Javascript by JQuery. Password hashing by PassLib.</p>
        </div>
        <div class="six columns">
          <ul class="link-list right">
            <li><a href="#">Section 1</a></li>
            
          </ul>
        </div>
      </div>
    </div> 
  </footer>
</body>
</html>