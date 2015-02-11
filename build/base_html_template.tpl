<!DOCTYPE html>
<html lang="en"> 
<head>
    <meta charset="utf-8"/>
    <meta http-equiv="X-UA-Compatible" content="IE=edge"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>

   
    <title>
    {% raw %}
        {% block title %}
            Page Title 
        {% endblock %}
    {% endraw %}
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

    {% raw %}
    {% block user_scripts %}
        <!-- placeholder for user-defined javscript code blocks -->
    {% endblock %}
    {% endraw %}
</head>
<body>
     <nav class="navbar navbar-default">
	<!-- container -->
	<div class="container-fluid">
          <!-- Brand and toggle get grouped for better mobile display -->
        <div class="navbar-header">
          <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1">
          <span class="sr-only">Toggle navigation</span>
          <span class="icon-bar"></span>
          <span class="icon-bar"></span>
          <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="#">Brand</a>
        </div>


          
	    <div class="row">
                <div class="col-md-2">
                  <h2>{{ config.app_name }}</h2>	
                </div>
                <div class="col-md-10">                 
                  <h5>version {{ config.app_version }}</h5>		
                </div>	
            </div> <!-- end row -->
        
        <div class="row" id="header">
            <div class="col-md-12">
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
                
                    <!-- Collect the nav links, forms, and other content for toggling -->
    <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
      <ul class="nav navbar-nav">
        <li class="active"><a href="#">Link <span class="sr-only">(current)</span></a></li>
        <li><a href="#">Link</a></li>
        <li class="dropdown">
          <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false">Dropdown <span class="caret"></span></a>
          <ul class="dropdown-menu" role="menu">
            <li><a href="#">Action</a></li>
            <li><a href="#">Another action</a></li>
            <li><a href="#">Something else here</a></li>
            <li class="divider"></li>
            <li><a href="#">Separated link</a></li>
            <li class="divider"></li>
            <li><a href="#">One more separated link</a></li>
          </ul>
        </li>
      </ul>
      <form class="navbar-form navbar-left" role="search">
        <div class="form-group">
          <input type="text" class="form-control" placeholder="Search">
        </div>
        <button type="submit" class="btn btn-default">Submit</button>
      </form>
    </div><!-- /.navbar-collapse -->
                
                {% endblock %}
                {% endraw %}
	  </div> 
         </div> <!-- end header div -->
		
		
		

		<div class="row">
		<div class="col-md-12">
                 <div class="panel panel-default">
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
     </nav>

</body>
</html>
