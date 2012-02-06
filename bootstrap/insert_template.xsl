<?xml version="1.0"?>
<!DOCTYPE xsl:stylesheet [
    <!ENTITY nbsp "&#160;">
]>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="html" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd" 
  doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN" indent="yes"/>
  
<xsl:template match="formspec">

{% extends "base_template.html" %}

{% block title %}
<xsl:value-of select="@model"/> Insert
{% endblock %}

{% block user_scripts %}
<script type="text/javascript" language="javascript">

    $document.ready(function(){
    
    });
    
</script>
{% endblock %}

{% block content_header %}
    <h2><xsl:value-of select="@model"/> Insert Page</h2>
    <h3>Add <xsl:value-of select="@model"/> objects</h3>
{% endblock %}


{% block content %}
        <form class="right_aligned" id='action_form' method="post">
          <xsl:attribute name="action">/<xsl:value-of select="@url_base"/>/controller/<xsl:value-of select="@model"/>/insert</xsl:attribute>		  
		  
            <xsl:apply-templates/>
		
		    <label for="submit_button">&nbsp;</label><input id="submit_button" type="submit" value="Save"/>
	     </form>
{% endblock %}

</xsl:template>

<xsl:template match="field">
    {{ form.<xsl:value-of select="name"/>.label }} {{ form.<xsl:value-of select="name"/>() }}
</xsl:template>


</xsl:stylesheet>
