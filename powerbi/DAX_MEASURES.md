# DAX measures

The source of truth is [measures.json](measures.json). The builder places these measures on the `DrugYear` table in `model.bim`; the folders below organize the field list. Raw fact columns are hidden so report authors use explicit measures.

**Validation status:** formulas are authored and their report references have been checked. Their execution must be verified in Power BI Desktop using [the nine-check query](validation/desktop_checks.dax). Python source controls do not prove DAX engine behavior.

## Filter and missing-value conventions

- Spending and fills retain the current drug and year filters.
- Share of listed spending clears only Drug filters from its denominator. It retains the same year selection.
- Previous-year comparisons require one observation year and retain the selected product or group. Missing current or prior values leave growth blank.
- `DIVIDE` returns blank for a missing or zero denominator. No artificial zero is substituted for unavailable history.
- The spending bridge requires one product and one year; mixed-product averages are not given a product-level interpretation.
- Dense product ranks can include ties. Validation controls intentionally ignore report selections.

## Spending

### Total spending

Sum of reported gross spending, converted from integer cents. Keeps current drug and year filters; excludes rebates.

```dax
Total spending =
DIVIDE(SUM('DrugYear'[SpendingCents]), 100)
```

### Prescription fills

Original prescriptions and refills in the current filter context. Not unique people or standardized treatment courses.

```dax
Prescription fills =
SUM('DrugYear'[Fills])
```

### Available products

Products with a published spending observation in the current selection. Count the fact-table keys so unavailable years do not inflate the count.

```dax
Available products =
DISTINCTCOUNT('DrugYear'[DrugKey])
```

### Average spending per fill

Weighted average: selected total gross dollars divided by selected fills. Do not average product-level averages. Returns blank without a usable denominator.

```dax
Average spending per fill =
DIVIDE([Total spending], [Prescription fills])
```

### Share of listed spending

Selected spending divided by all listed products in the same selected year(s). Clears drug filters only, including group, ingredient, brand and product.

```dax
Share of listed spending =
DIVIDE([Total spending], CALCULATE([Total spending], REMOVEFILTERS('Drug')))
```

## Growth

### Prior-year spending

Previous calendar observation year for the same drug selection. Requires one selected year; 2020 has no 2019 baseline in this release.

```dax
Prior-year spending =
VAR Y = SELECTEDVALUE('Year'[Year])
RETURN IF(NOT ISBLANK(Y), CALCULATE([Total spending], REMOVEFILTERS('Year'), 'Year'[Year] = Y - 1))
```

### Prior-year fills

Published fills in the previous observation year. Missing history stays blank.

```dax
Prior-year fills =
VAR Y = SELECTEDVALUE('Year'[Year])
RETURN IF(NOT ISBLANK(Y), CALCULATE([Prescription fills], REMOVEFILTERS('Year'), 'Year'[Year] = Y - 1))
```

### Prior-year average per fill

Prior-year gross dollars divided by prior-year fills within the same drug selection.

```dax
Prior-year average per fill =
DIVIDE([Prior-year spending], [Prior-year fills])
```

### Spending change

Current minus prior spending only when both are observed. Aggregate changes can include changes in product availability.

```dax
Spending change =
VAR Current = [Total spending]
VAR Prior = [Prior-year spending]
RETURN IF(NOT ISBLANK(Current) && NOT ISBLANK(Prior), Current - Prior)
```

### Spending YoY

Reported spending change divided by positive prior-year spending. Blank for missing or zero prior spending, or an ambiguous year selection.

```dax
Spending YoY =
DIVIDE([Spending change], [Prior-year spending])
```

### Fills YoY

Change in fill count over the prior year. A small starting count can produce a very large percentage.

```dax
Fills YoY =
VAR Current = [Prescription fills]
VAR Prior = [Prior-year fills]
RETURN IF(NOT ISBLANK(Current) && NOT ISBLANK(Prior), DIVIDE(Current - Prior, Prior))
```

### Average per fill YoY

Change in average gross spending per fill. Supply and mix affect this measure; it is not a standardized unit-price change.

```dax
Average per fill YoY =
VAR Current = [Average spending per fill]
VAR Prior = [Prior-year average per fill]
RETURN IF(NOT ISBLANK(Current) && NOT ISBLANK(Prior), DIVIDE(Current - Prior, Prior))
```

## Bridge

### Fill-volume component

Volume-first component: (current fills - prior fills) × prior average spend/fill. Requires one product and two observed years. An arithmetic component, not a causal effect.

```dax
Fill-volume component =
VAR Valid = HASONEVALUE('Drug'[Product]) && HASONEVALUE('Year'[Year]) && NOT ISBLANK([Prior-year spending]) && NOT ISBLANK([Total spending]) && [Prior-year fills] > 0 && [Prescription fills] > 0
RETURN IF(Valid, ([Prescription fills] - [Prior-year fills]) * [Prior-year average per fill])
```

### Average-spend component

Second component: current fills × (current average - prior average). Includes supply and product mix; does not isolate a pure price effect.

```dax
Average-spend component =
VAR Valid = HASONEVALUE('Drug'[Product]) && HASONEVALUE('Year'[Year]) && NOT ISBLANK([Prior-year spending]) && NOT ISBLANK([Total spending]) && [Prior-year fills] > 0 && [Prescription fills] > 0
RETURN IF(Valid, [Prescription fills] * ([Average spending per fill] - [Prior-year average per fill]))
```

### Bridge residual

Volume plus average component minus total change. Should be zero to the nearest cent when the bridge is defined.

```dax
Bridge residual =
VAR Volume = [Fill-volume component]
VAR Average = [Average-spend component]
RETURN IF(NOT ISBLANK(Volume) && NOT ISBLANK(Average), Volume + Average - [Spending change])
```

## Context

### Comparison context

Visible guidance for missing comparisons, multi-selection, and fewer than 1,000 prior-year fills. The threshold is an explanatory portfolio rule, not a CMS suppression rule.

```dax
Comparison context =
VAR Prior = [Prior-year fills]
RETURN SWITCH(TRUE(), NOT HASONEVALUE('Year'[Year]), "Select one observation year to calculate annual growth.", NOT HASONEVALUE('Drug'[Product]), "Select one product for the spending-change bridge.", ISBLANK([Prior-year spending]) || ISBLANK([Total spending]), "Comparison unavailable: both current and prior spending must be observed.", Prior < 1000, "Small baseline: " & FORMAT(Prior, "#,0") & " prior-year fills. Growth percentages are sensitive to that starting point.", "Components reconcile before rounding. Average spending reflects supply and mix; the bridge is not a causal price estimate.")
```

## Ranking

### Spending rank

Dense rank within the user-selected drug population. Ties can produce more than ten products in the leading-ten-ranks chart.

```dax
Spending rank =
IF(NOT ISBLANK([Total spending]), RANKX(ALLSELECTED('Drug'[Product]), [Total spending], , DESC, DENSE))
```

### Leading product spending

Returns spending for the leading ten ranks, preserving slicer selection. Other products return blank.

```dax
Leading product spending =
VAR Rank = [Spending rank]
RETURN IF(NOT ISBLANK(Rank) && Rank <= 10, [Total spending])
```

## Validation

### Release products

Count of available products in the 2024 release, independent of report slicers.

```dax
Release products =
CALCULATE([Available products], REMOVEFILTERS('Drug'), REMOVEFILTERS('Year'), 'Year'[Year] = 2024)
```

### Release observations

Count of nonmissing product-year rows across all five years.

```dax
Release observations =
CALCULATE(COUNTROWS('DrugYear'), REMOVEFILTERS('Drug'), REMOVEFILTERS('Year'))
```

### Release reconciliation

Compares refreshed all-product and selected-group spending and the product count against independent Python/SQL source controls. This is a release-specific check, not a live-market completeness guarantee.

```dax
Release reconciliation =
VAR AllSpend = CALCULATE([Total spending], REMOVEFILTERS('Drug'), REMOVEFILTERS('Year'), 'Year'[Year] = 2024)
VAR GroupSpend = CALCULATE([Total spending], REMOVEFILTERS('Drug'), REMOVEFILTERS('Year'), 'Year'[Year] = 2024, 'Drug'[Drug group] = "GLP-1 / GIP")
RETURN IF(ISBLANK(AllSpend), "Refresh to load the public source", IF(ABS(AllSpend - 288667842058.40) < 0.01 && ABS(GroupSpend - 27513350127.66) < 0.01 && [Release products] = 3625, "PASS · 2024 source totals match", "REVIEW · source totals differ"))
```

References: Microsoft documents [DIVIDE](https://learn.microsoft.com/en-us/dax/divide-function-dax), [REMOVEFILTERS](https://learn.microsoft.com/en-us/dax/removefilters-function-dax), [SELECTEDVALUE](https://learn.microsoft.com/en-us/dax/selectedvalue-function-dax), and [ALLSELECTED](https://learn.microsoft.com/en-us/dax/allselected-function-dax).
