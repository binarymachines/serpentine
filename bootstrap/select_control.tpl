
<select name="{{ control.name  }}" id="{{ control.id }}"
{% if control.cssClass is not none %}class="{{ control.cssClass }}"{% endif %}
{% if control.css is not none %}style="{{ control.css }}"{% endif %}>
{% for item in options %} 
    <option value="{{ item.value }}">{{ item.name }}</option>
{% endfor %} 
</select>