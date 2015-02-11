{% raw %}{% extends "base_template.html" %}{% endraw %}

{% raw %}{% block title %}{% endraw %}
{{ formspec.model }} Delete
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
    <h5>Delete {{ formspec.model }}</h5>
    <p>Confirmation page for {{ formspec.model }} deletion</p>
{% raw %}{% endblock %}{% endraw %}


{% raw %}{% block content %}{% endraw %}
        <form role="form" class="nice" id="action_form" method="post" 
        action="/{{ config.url_base }}/controller/{{ formspec.model }}/delete/{% raw %}{{form.id.data}}{% endraw %}">
		   <div class="form-group">
		    <label for="id">ID</label><input name="id" value="{% raw %}{{ form.id.data }}{% endraw %}" class="input-text" disabled="disabled"/>
		    </div>
            {% for field in formspec.fields %}
            <div class="form-group">
            {% raw %} {{ {% endraw %}form.{{ field.name }}.label {% raw %} }} {% endraw %}
            {% raw %} {{ {% endraw %}form.{{ field.name }}(class="input-text", disabled="disabled") {% raw %} }} {% endraw %}
            </div>
            {% endfor %}
        
		
		    <label for="submit_button">Are you sure you want to delete this {{formspec.model}}?</label><input id="submit_button" type="submit" value="Yes; Delete"/><input id="cancel_button" type="button" class="btn btn-success" value="No; Cancel"/>
	     </form>
{% raw %}{% endblock %}{% endraw %}
