<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="html" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd" 
  doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN" indent="yes"/>
  
<xsl:template match="formspec">

<html xmlns="http://www.w3.org/1999/xhtml">
	<head>
	    <title><xsl:value-of select="@model"/> Update</title>
     </head>
<body>

<div id="content_container">
 <div id="content_header">
   <h2>
    <xsl:value-of select="@model"/> Update Page
   </h2>
   <p>Change <xsl:value-of select="@model"/> objects</p>
</div>
   <div id="content">
        <form class="right_aligned" id='action_form' method="post">
          <xsl:attribute name="action">/<xsl:value-of select="@url_base"/>/controller/<xsl:value-of select="@model"/>/update</xsl:attribute>
		  {{ form.mode() }}
		  {{ form.id() }}
            <xsl:apply-templates/>
		
		    <label></label><input type="submit" value="Save"/>
	     </form>

   </div>
</div>
<div id="footer">Footer</div>

</body>
</html>

</xsl:template>

<xsl:template match="field">
    {{ form.<xsl:value-of select="name"/>.label }} {{ form.<xsl:value-of select="name"/>() }}
</xsl:template>


</xsl:stylesheet>
