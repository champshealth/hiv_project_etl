{% macro impl_expect_column_values_to_not_be_null(model, column_name, row_condition=None) %}

{# Build SQL with optional row_condition filter #}
{% set where_clause = "WHERE " ~ column_name ~ " IS NULL" %}
{% if row_condition is not none %}
    {% set where_clause = where_clause ~ " AND (" ~ row_condition ~ ")" %}
{% endif %}

{# Return failing records #}
SELECT 
    TOP 100 *  -- Limit to 100 rows to avoid large result sets
FROM 
    {{ model }}
{{ where_clause }}

{% endmacro %}