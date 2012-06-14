{% raw %}{% extends "base_template.html" %}{% endraw %}

{% raw %}{% block title %}{% endraw %}
{{ formspec.model }} Index
{% raw %}{% endblock %}{% endraw %}


{% raw %}{% block user_scripts %}{% endraw %}
<script type="text/javascript" language="javascript">

    $(document).ready(function(){
        
        //stripe("index_table");
        
        /* 
        The 'action-registration' pattern makes the logic of selects and prompts easier, 
        more direct, and less error-prone.  For every registered action in
        the hashtable 'actions', there are the following values: 
        
        'name': the string ID of the chosen select option -- this is the index into the hashtable
        'url': the (usually relative) url that should be triggered on clicking the Go button
        'params': a hashtable mapping variable names embedded in the url to values (or functions to retrieve them)
        'must_select': a boolean value specifying whether a record must be selected before clicking Go
        */
        
        actions = {};
        registerAction(actions, "add", "/{{ config.url_base }}/controller/{{ formspec.model }}/insert", {}, false);                                
        registerAction(actions, "update", "/{{ config.url_base }}/controller/{{ formspec.model }}/update/{id}", 
                        { "id":  getObjectID }, 
                        true);
        initTableSelectLogic(actions);

    });
    
</script>
{% raw %}{% endblock %} {% endraw %}

{% raw %}{% block content_header %}{% endraw %}
    <h5>{{ formspec.model }} Index Page</h5>
    <p>List of all {{ formspec.model }} objects in the system</p>
{% raw %}{% endblock %}{% endraw %}

{% raw %}{% block content %}{% endraw %}
<form action="#" method="GET" id="action_form">
    <select name="action" id="action_selector">  			  
      			<option id="add" value="#">Add</option>
      			<option id="update" value="#">Update</option>    	      		    
    </select>
    <button id="go_button" type="submit" style="width: 4em; height: 2em">Go</button>

    <table id="index_table">
        <thead>            
            <th>Select</th>
            {% for field in formspec.fields %}<th>{{ field.label }}</th>{% endfor %}               
        </thead>
        <tbody>    
        {% raw %}{% for record in resultset %}{% endraw %}
            <tr>
              <td>
                <input type="radio" class="object_id_button" name="object_id" value="{% raw %}{{ record.id }}{% endraw %}"/>
              </td>
                {% for field in formspec.fields %}<td>{% raw %} {{ {% endraw %}record.{{ field.name }} {% raw %} }} {% endraw %}</td>{% endfor %}
            </tr>
        {% raw %}{% endfor %}{% endraw %}
        </tbody>
     </table>

</form>
{% raw %}{% endblock %}{% endraw %}



