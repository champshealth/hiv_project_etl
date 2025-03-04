{% test expect_column_values_to_not_be_null(model, column_name, row_condition=None) %}
    {{ return(impl_expect_column_values_to_not_be_null(model, column_name, row_condition)) }}
{% endtest %}