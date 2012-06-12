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
    <h2>{{ formspec.model }} Insert Page</h2>
    <h3>Add {{ formspec.model }} objects</h3>
{% raw %}{% endblock %}{% endraw %}


{% raw %}{% block content %}{% endraw %}
        <form class="right_aligned" id='action_form' method="post" action="/{{ config.url_base }}/controller/{{ formspec.model }}/insert"		  
		  
            {% for field in formspec.fields %}
            {% if field.name != 'id' %}
            {% raw %} {{ {% endraw %}form.{{ field.name }}.label {% raw %} }} {% endraw %}{% raw %} {{ {% endraw %}form.{{ field.name }}() {% raw %} }} {% endraw %}<br/>
            {% endif %}
            {% endfor %}
		
		    <label for="submit_button">&nbsp;</label><input id="submit_button" type="submit" value="Save"/>
	     </form>
{% raw %}{% endblock %}{% endraw %}

