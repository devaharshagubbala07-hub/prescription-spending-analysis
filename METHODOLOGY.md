# Methodology

## Source and population

Use the exact CMS June 2026 CSV pinned in [source.json](source.json). CMS describes its grain, exclusion rules, gross spending basis, and unit-spend flags in the [official methodology](https://data.cms.gov/sites/default/files/2026-06/d7e0a571-9d08-40ec-8278-1b2300f59424/DSD_PTD_RY26_20260603_Methodology_WDDSE_508.pdf) and [dictionary](https://data.cms.gov/sites/default/files/2026-06/Medicare%20Part%20D%20Spending%20by%20Drug%20Data%20Dictionary%2020260603_508.pdf).

Keep `Mftr_Name == Overall` only. Reject duplicate brand + ingredient Overall rows. Transform the 2020–2024 columns into brand + ingredient + year records. Missing spending cells do not become zeros. Validate positive claim denominators, nonnegative finite numbers, whole counts, and allowed outlier flags.

The resulting grain is one reported drug product in one observation year. This is aggregate public data; no patient-level inference or linkage is performed.

## Scope

The selected cohort matches these exact, case-insensitive ingredient names: semaglutide, tirzepatide, dulaglutide, liraglutide, exenatide, exenatide microspheres, lixisenatide. It is an explicitly selected analytical group, not a comprehensive clinical ontology. Insulin combinations are excluded. A string ending in “glutide” is not sufficient for inclusion. Only products present in the CMS source can appear.

The `all` scope contains every Overall product listed in this release. Earlier-year summaries are affected by the latest-year inclusion rules and historical suppression. They are not a complete historical market total.

## Measures

| Measure | Calculation |
|---|---|
| Gross spending | Sum of published spending, stored as integer cents |
| Prescription fills | Sum of original and refill claim counts |
| Average spending / fill | Total selected dollars / total selected fills |
| Selected spending share | Selected dollars / all listed-product dollars for the same year |
| Top-10 share | Top ten selected products' dollars / selected dollars |
| Unit-spend flag | Preserve CMS's flag; do not interpret it as invalid total spending |

Beneficiaries are retained at product/year level in the exports but are not summed across products. CMS's weighted dosage-unit measure is retained as a source field; it is not replaced by a crude spending/units ratio and is not compared across ingredients.

## Spending-change bridge

For one product with nonmissing positive fill counts in both 2023 and 2024, let Q be fill count, S be gross spending, and A = S/Q.

1. Claim-count component = (Q2024 − Q2023) × A2023.
2. Average-spend component = Q2024 × (A2024 − A2023).
3. The two components sum to S2024 − S2023.

This ordering assigns the interaction to the average-spend component. Another decomposition can allocate it differently. Decimal arithmetic verifies the identity before display rounding. “Average spend” is not a pure price effect: days supplied, strength, dosage form, and other mix changes may contribute. Missing baselines produce no bridge.

## Checks and sensitivity

Checks reconcile source partitions, unique keys, historical availability, annual dollars, selected-cohort inclusion, and bridge components. Tests cover manufacturer duplication, missingness, duplicate keys, monetary parsing, the bridge identity, missing baselines, and ingredient inclusion boundaries.

To extend the work, compare cohort definitions and examine individual products' histories. Do not extrapolate Medicare costs to an employer plan without an appropriate population and additional evidence. No 2025/2026 spend forecast, rebate estimate, treatment comparison, or policy savings estimate is produced.
