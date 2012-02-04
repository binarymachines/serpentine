

from wtforms import Form, BooleanField, TextField, PasswordField
from wtforms import TextAreaField, IntegerField, HiddenField 
from wtforms import SelectField, FormField, DateField, validators
from wtforms.widgets import SubmitInput




{% for spec in formspecs %}

class {{ spec.formClassName }}(Form):
      {% for field in spec.fields %} {{ field }}
      {% endfor%}

{% endfor %}
