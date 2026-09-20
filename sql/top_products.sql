SELECT brand, generic, spend_cents, claims, beneficiaries,
       weighted_unit_spend, unit_outlier
FROM drug_years
WHERE year = :year AND (:cohort = 'all' OR selected_incretin = 1)
ORDER BY spend_cents DESC, brand, generic LIMIT 10;
