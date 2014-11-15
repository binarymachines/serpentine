
{% for item in options %} 
<input type="radio" name="{{ control.name }}" value="{{ item.value }}" 
{% if control.cssClass is not none %}class="{{ control.cssClass }}"{% endif %}
{% if control.css is not none %}style="{{ control.css }}"{% endif %}/>{{ item.name }}
{% endfor %} 