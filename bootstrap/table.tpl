
<table name="{{ control.name  }}" id="{{ control.id }}" {% if control.cssClass is not none %}class="{{ control.cssClass }}"{% endif %}{% if control.style is not none %}style="{{ control.style }}"{% endif %}>

<thead>
{% for field in data.header %}
<th>{{ field }}</th>{% endfor %}
</thead>
<tbody>
{% for record in data.records %} 
<tr>
{% for field in record %}
<td>{{ field }}</td>{% endfor %}
</tr>
{% endfor %} 
</tbody>
</table>