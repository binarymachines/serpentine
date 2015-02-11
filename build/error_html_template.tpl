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
        <h3>Error.</h3>
        <p>{{ config.app_name }} error handler page</p>
      </div>
    </div>
  </div>
  
  <!-- End Header and Nav -->
  
  
  <div class="row" style="margin-top: 100px; margin-bottom: 100px">    
    
    <!-- Main Feed -->
    <!-- This has been source ordered to come first in the markup (and on small devices) but to be to the right of the nav on larger screens -->
    <div class="col-md-8">
      
      <!-- Feed Entry -->
      <div class="row">
        <div class="col-md-1"><span class="glyphicon glyphicon-remove-circle" style="font-size:28pt; color:red"></span></div>
        <div class="col-md-11">
          <h6><strong>Exception: {% raw %}{{exception.__class__.__name__}}{% endraw %}.</strong></h6>
          ({% raw %}{{exception.message}}{% endraw %})</p>
          
          
          <h6><strong>Stacktrace:</strong></h6>
          {% raw %}
          {% for entry in stacktrace %}
          <div class="row">            
            <div class="col-md-12">
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
    <div class="col-md-12">
      <hr />
      <div class="row">
        <div class="col-md-6">
          <p>The Serpentine open-source Python stack. New from Binary Machines. HTTP request handling by bottle. Forms by WTForms. Templates by Jinja2. ORM by SQLAlchemy. HTML/CSS by Foundation. Javascript by JQuery. Password hashing by PassLib.</p>
        </div>
        <div class="col-md-6">
          <ul class="link-list right">
            <li><a href="#">Section 1</a></li>
            
          </ul>
        </div>
      </div>
    </div> 
  </footer>
</body>
</html>