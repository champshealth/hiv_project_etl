{% test assert_table_has_rows(model, min_rows=1) %}
    {{ return(impl_assert_table_has_rows(model, min_rows)) }}
{% endtest %}