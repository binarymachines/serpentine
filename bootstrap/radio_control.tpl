
{% for item in options %} 
<input type="radio" name="{{ control.name }}" value="{{ item.value }}"/>{{ item.name }}
{% endfor %} 