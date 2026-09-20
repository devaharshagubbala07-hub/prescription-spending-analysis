-- One row per brand/generic/year. Manufacturer detail is excluded upstream.
SELECT year, COUNT(*) AS products, SUM(spend_cents) AS spend_cents,
       SUM(claims) AS claims,
       SUM(CASE WHEN unit_outlier = 1 THEN 1 ELSE 0 END) AS unit_outlier_products
FROM drug_years
WHERE (:cohort = 'all' OR selected_incretin = 1)
GROUP BY year ORDER BY year;
