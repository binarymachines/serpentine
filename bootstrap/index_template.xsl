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

    $document.ready(function(){
    
    });
    
</script>
{% endblock %} 

{% block content_header %}
    <h2><xsl:value-of select="@model"/> Index Page</h2>
    <h3>List of all <xsl:value-of select="@model"/> Objects in the system</h3>
{% endblock %}

{% block content %}
    <table id="index_table">
        <thead>            
            <th>Select</th>
            <xsl:for-each select="field">
            <th><xsl:value-of select="label"/></th>    
            </xsl:for-each>            
        </thead>
        <tbody>    

        {% for record in resultset %}
            <tr>
              <td>
                <input type="radio" class="object_id_button" name="object_id" value="{@id}"/>
              </td>
              <xsl:apply-templates/>
            </tr>
        {% endfor %}
        </tbody>
     </table>
{% endblock %}

</xsl:template>

<xsl:template match="field">
    <td>{{ record.<xsl:value-of select="name"/> }}</td>
</xsl:template>


</xsl:stylesheet>
