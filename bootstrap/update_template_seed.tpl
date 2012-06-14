{% raw %}{% extends "base_template.html" %}{% endraw %}

{% raw %}{% block title %}{% endraw %}
{{ formspec.model }} Update
{% raw %}{% endblock %}{% endraw %}


{% raw %}
{% block user_scripts %}
<script type="text/javascript" language="javascript">

    $(document).ready(function(){
    
    });
    
</script>
{% endblock %}
{% endraw %}


{% raw %}{% block content_header %}{% endraw %}
    <h5>Update {{ formspec.model }}</h5>
    <p></p>
{% raw %}{% endblock %}{% endraw %}


{% raw %}{% block content %}{% endraw %}
        <form class="nice" id="action_form" method="post" action="/{{ config.url_base }}/controller/{{ formspec.model }}/update">
		  
            {% for field in formspec.fields %}
            {% if field.name != 'id' %}
            {% raw %} {{ {% endraw %}form.{{ field.name }}.label {% raw %} }} {% endraw %}{% raw %} {{ {% endraw %}form.{{ field.name }}() {% raw %} }} {% endraw %}
            {% endif %}
            {% endfor %}
		
		    <label for="submit_button">&nbsp;</label><input id="submit_button" type="submit" value="Save"/>
	     </form>
{% raw %}{% endblock %}{% endraw %}
