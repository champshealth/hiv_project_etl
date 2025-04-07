{% test champs_id_format(model, column_name) %}
    {{ return(impl_champs_id_format(model, column_name)) }}
{% endtest %}