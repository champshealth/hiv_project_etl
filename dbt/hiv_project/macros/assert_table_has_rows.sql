{% macro impl_assert_table_has_rows(model, min_rows=1) %}

{# Return records where we fail the test #}
select
    TOP 1 1 as fail_indicator
from 
    (
        -- Check we have at least min_rows
        select count(*) as row_count
        from {{ model }}
    ) counts
where 
    counts.row_count < {{ min_rows }}

{% endmacro %}