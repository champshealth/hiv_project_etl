{% test date_is_before_current(model, column_name) %}
    {{ return(impl_date_is_before_current(model, column_name)) }}
{% endtest %}