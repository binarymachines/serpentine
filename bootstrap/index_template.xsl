<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="html" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd" 
  doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN" indent="yes"/>
  
<xsl:template match="formspec">

{% extends "base_template.html" %}

{% block title %}
<xsl:value-of select="@model"/> Index
{% endblock %}

{% block user_scripts %}
<script type="text/javascript" language="javascript">

    $(document).ready(function(){
        
        stripe("index_table");
        
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
        registerAction(actions, "add", "/add_operation_url", {}, false);                                
        registerAction(actions, "update", "/update_operation_url/{id}", 
                        { "id":  getObjectID }, 
                        true);
        initTableSelectLogic(actions);

    });
    
</script>
{% endblock %} 

{% block content_header %}
    <h2><xsl:value-of select="@model"/> Index Page</h2>
    <h3>List of all <xsl:value-of select="@model"/> Objects in the system</h3>
{% endblock %}

{% block content %}
<form action="#" method="GET" id="action_form">
    <select name="action" id="action_selector">  			  
      			<option id="add" value="#">Add</option>
      			<option id="update" value="#">Update</option>    	      		    
    </select>
    <button id="go_button" type="submit" style="width: 4em; height: 2em">Go</button>

    <table id="index_table">
        <thead>            
            <th>Select</th>
            <xsl:for-each select="field"><th><xsl:value-of select="label"/></th>    
            </xsl:for-each>            
        </thead>
        <tbody>    
        {% for record in resultset %}
            <tr>
              <td>
                <input type="radio" class="object_id_button" name="object_id" value="{{ record.id }}"/>
              </td>
                <xsl:apply-templates/>
            </tr>
        {% endfor %}
        </tbody>
     </table>
</form>
{% endblock %}

</xsl:template>

<xsl:template match="field">
    <td>{{ record.<xsl:value-of select="name"/> }}</td>
</xsl:template>


</xsl:stylesheet>
