{% macro impl_champs_id_format(model, column_name) %}
select
    *
from {{ model }}
where {{ column_name }} is not null
  and (
    LEN({{ column_name }}) != 9
    or SUBSTRING({{ column_name }}, 1, 4) NOT LIKE '[A-Z][A-Z][A-Z][A-Z]'
    or SUBSTRING({{ column_name }}, 5, 5) NOT LIKE '[0-9][0-9][0-9][0-9][0-9]'
  )
{% endmacro %}

{% macro impl_date_is_before_current(model, column_name) %}
select
    *
from {{ model }}
where {{ column_name }} is not null
  and {{ column_name }} > GETDATE()
{% endmacro %}