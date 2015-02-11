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

	
	<title>
    
        {% block title %}
            {{ config.app_name }} Access-Denied Page
        {% endblock %}
    
    </title>
  
    <!-- Included CSS Files -->
    <!-- Bootstrap -->
    <link href="/{{ config.url_base }}/static/css/bootstrap.min.css" rel="stylesheet">

    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements
    and media queries (TODO: add to Serpentine dist)-->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
      <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->

    <script type="text/javascript" src="/{{ config.url_base }}/static/js/jquery.min.js"></script>
    <script type="text/javascript" src="/{{ config.url_base }}/static/js/serpentine.js"></script>
    
    <!-- Include all compiled plugins (below), or include individual files as needed -->
    <script src="/{{ config.url_base }}/static/js/bootstrap.min.js"></script>    
    
    
    {% block user_scripts %}
        <!-- placeholder for user-defined javscript code blocks -->
    {% endblock %}
    
</head>
<body>
<!-- Header and Nav -->
  
  <div class="row">
    <div class="col-md-12">
      <div class="panel">
        <h3>Access Denied.</h3>
        <p>{{ config.app_name }} error handler page</p>
      </div>
    </div>
  </div>
  
  <!-- End Header and Nav -->
  
  
  <div class="row" style="margin-top: 100px; margin-bottom: 100px">    
    

    <div class="col-md-8">
      
      <!-- Feed Entry -->
      <div class="row">
        <div class="col-md-1"><span class="glyphicon glyphicon-ban-circle" aria-hidden="true"></span></div>
        <div class="col-md-11">
          <h6><strong>{{ config.app_name }} security message: Access Denied.</strong></h6>
          <p>You do not have the security privileges to access the page you requested.</p>

        </div>
      </div>
      <!-- End Feed Entry -->
     
    </div>
  </div>
    
  
  <!-- Footer -->
  
  <footer class="row">
    <div class="col-md-12">
      <hr />
      <div class="row">
        <div class="col-md-6">
          <p>The Serpentine open-source Python stack. New from Binary Machines. HTTP request handling by bottle. Forms by WTForms. Templates by Jinja2. ORM by SQLAlchemy. HTML/CSS by Foundation. Javascript by JQuery. Password hashing by PassLib.</p>
        </div>
        <div class="col-md-6">
          ...
        </div>
      </div>
    </div> 
  </footer>
</body>
</html>