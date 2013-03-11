<table name="{{ control.name  }}" id="{{ control.id }}" {% if control.cssClass is not none %}class="{{ control.cssClass }}"{% endif %}{% if control.style is not none %}style="{{ control.style }}"{% endif %}>
{% block table_header %}
    <thead>
    <th>Select</th>
    {% for field in data.header %}
    <th>{{ field }}</th>{% endfor %}
    </thead>
{% endblock %}
{% block table_body %}
    <tbody>
        {% for record in data.records %} 
        <tr><td><input type="radio" class="object_id_button" name="object_id" value="{{record.id}}"/></td>{% for field in record %}<td>{{ field }}</td>{% endfor %}</tr>
        {% endfor %} 
    </tbody>
{% endblock %}
</table>