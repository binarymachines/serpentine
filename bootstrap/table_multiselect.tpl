<table name="{{ control.name  }}" id="{{ control.id }}" {% if control.cssClass is not none %}class="{{ control.cssClass }}"{% endif %}{% if control.style is not none %}style="{{ control.style }}"{% endif %}>
{% block table_head_element %}
    <thead>
    <th>Select</th>{% for field in data.header %}
    <th>{{ field }}</th>{% endfor %}
    </thead>
{% endblock %}
{% block table_body_element %}
    <tbody>
        {% for record in data.records %} 
        <tr><td><input type="checkbox" name="object_id" class="object_id_button" value="{{ record.id }}"/></td>{% for field in record %}<td>{{ field }}</td>{% endfor %}</tr>
        {% endfor %} 
    </tbody>
{% endblock %}
</table>