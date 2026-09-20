# Findings from the pinned CMS release

Source: [CMS Medicare Part D Spending by Drug](https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-medicaid-spending-by-drug/medicare-part-d-spending-by-drug), released 2026-06-25; observation years 2020–2024. This is public aggregate data, analyzed with AI assistance.

## What stands out

- The 3,625 listed products have **$288.67 billion** in reported gross spending for 2024. The ten largest account for **28.5%** of that listed-product total.
- The explicitly selected single-agent GLP-1 / GIP cohort accounts for **$27.51 billion**, or **9.5%** of listed-product spending. Insulin combination products are excluded by design.
- Ozempic gross spending increased **$3.78 billion** between 2023 and 2024. The arithmetic bridge attributes **$4.63 billion** to the change in claim count at 2023 average spending, and **$-0.85 billion** to the subsequent change in average spending per claim at 2024 claim volume.

## How to use the findings

Start a budget discussion with spending concentration and changes in claim volume. For a specific drug, inspect average spending per claim alongside claim counts. A rise in total spending can occur while average spending per claim falls. This decomposition describes the arithmetic; it does not establish the causes.

## Limits that matter

This release excludes drugs with fewer than 11 claims in 2024. Historical cells can be redacted; missing cells are never zero-filled. Earlier-year totals describe the products visible in this release, not a complete historical market census. Spending is gross and excludes manufacturer rebates. Medicare results do not represent an employer population. A claim is a prescription fill, with varying days supplied; average spending per claim is not a standardized unit price. Beneficiaries overlap across products and are not summed into a unique-person total. The data does not identify treatment indication, adherence, health outcomes, or a suitable treatment for any individual.

## Reproduce and challenge it

Run `python analysis.py` and `python -m unittest discover -s tests -v`. Check `source.json`, the SQL files, and `METHODOLOGY.md`. Try changing the explicit cohort definition; retain the missing-value rules and avoid adding manufacturer rows to the Overall summaries.
