<?xml version="1.0"?>
<formspec model="{{ formspec.model }}" url_base="{{ formspec.urlBase }}">
    {% for field in formspec.fields %}
    <field required="{{ field.required }}" hidden="{{ field.hidden }}">
        <label>{{ field.label }}</label>
        <name>{{ field.name }}</name>
        <type>{{ field.type.__name__ }}</type>
    </field>
    {% endfor %}
</formspec>
