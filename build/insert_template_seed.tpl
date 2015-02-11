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
    <p></p>
{% raw %}{% endblock %}{% endraw %}


{% raw %}{% block content %}{% endraw %}
        <form role="form" id="action_form" method="post" action="/{{ config.url_base }}/controller/{{ formspec.model }}/insert">		  
		  
            {% for field in formspec.fields %}
            {% if field.name != 'id' %}
            <div class="form-group">
            {% raw %} {{ {% endraw %}form.{{ field.name }}.label {% raw %} }} {% endraw %}
            {% raw %} {{ {% endraw %}form.{{ field.name }}(class="input-text") {% raw %} }} {% endraw %}
            {% endif %}
            </div>
            {% endfor %}
		
		    <label for="submit_button">&nbsp;</label>
            <button id="submit_button" type="submit" value="Save" class="btn btn-success"/>
	     </form>
{% raw %}{% endblock %}{% endraw %}

