{% test test_soft_delete_percentage(model, max_percentage=25) %}
    {{ return(impl_test_soft_delete_percentage(model, max_percentage)) }}
{% endtest %}