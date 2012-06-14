{% raw %}{% extends "base_template.html" %}{% endraw %}

{% raw %}{% block title %}{% endraw %}
{{ formspec.model }} Insert
{% raw %}{% endblock %}{% endraw %}


{% raw %}{% block user_scripts %}{% endraw %}
<script type="text/javascript" language="javascript">

    $(document).ready(function(){
    
    });
    
</script>
{% raw %}{% endblock %}{% endraw %}


{% raw %}{% block content_header %}{% endraw %}
    <h5>Insert {{ formspec.model }}</h5>
{% raw %}{% endblock %}{% endraw %}


{% raw %}{% block content %}{% endraw %}
        <form class="nice" id="action_form" method="post" action="/{{ config.url_base }}/controller/{{ formspec.model }}/insert">		  
		  
            {% for field in formspec.fields %}
            {% if field.name != 'id' %}
            {% raw %} {{ {% endraw %}form.{{ field.name }}.label {% raw %} }} {% endraw %}{% raw %} {{ {% endraw %}form.{{ field.name }}() {% raw %} }} {% endraw %}
            {% endif %}
            {% endfor %}
		
		    <label for="submit_button">&nbsp;</label><input id="submit_button" type="submit" value="Save"/>
	     </form>
{% raw %}{% endblock %}{% endraw %}

