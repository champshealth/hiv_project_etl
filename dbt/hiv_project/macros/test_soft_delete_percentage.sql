{% macro impl_test_soft_delete_percentage(model, max_percentage=25) %}

-- This query selects records only if too many records are soft-deleted
WITH deletion_stats AS (
    SELECT
        COUNT(*) AS total_count,
        SUM(CASE WHEN IsDeleted = 1 THEN 1 ELSE 0 END) AS deleted_count
    FROM {{ model }}
)
SELECT
    'Too many soft-deleted records' AS failure_reason,
    deleted_count AS deleted_records,
    total_count AS total_records,
    (deleted_count * 100.0) / total_count AS deleted_percentage
FROM deletion_stats
WHERE 
    -- Only return rows when the test fails (deleted percentage exceeds threshold)
    -- This causes the test to fail when rows are returned
    total_count > 0 AND
    (deleted_count * 100.0) / total_count > {{ max_percentage }}

{% endmacro %}