# Prescription spending & GLP-1 trends

**[Explore the analysis](https://devaharshagubbala07-hub.github.io/projects/prescription-spending/)** · [Findings](outputs/findings.md) · [Methodology](METHODOLOGY.md) · [Walkthrough](WALKTHROUGH.md)

A new analyst portfolio project using **real public CMS aggregate data**, developed with AI assistance. It asks which products concentrate prescription spending and how changes in fill counts and average spending per fill contribute to a drug's spending change.

## Data freshness

- **Publisher:** Centers for Medicare & Medicaid Services.
- **Release:** June 25, 2026; retrieved September 20, 2026.
- **Observations:** 2020–2024 columns in the 2024 release. These are not 2026 spending observations.
- **Coverage:** 3,625 Overall brand/ingredient summaries; manufacturer-detail rows are excluded to avoid duplication.
- **Basis:** reported gross spending, before manufacturer rebates or price concessions.

The [source manifest](source.json) records the download, documentation, release date, and exact SHA-256 checksum. CMS methodology and inclusion rules are linked there. The analysis contains no employer or patient records.

## What is included

- A pinned-source downloader, wide-to-long transformation, and integer-cent spending calculations.
- SQL cohort summaries and top-product queries.
- An explicit single-agent GLP-1/GIP cohort, including tirzepatide and excluding insulin combinations.
- A claim-count / average-spend decomposition for comparable 2023–2024 drug observations.
- An interactive dashboard with group/year filters, individual-drug histories, and CSV export.
- Seven analytical tests, six reconciliation checks, and a source-grounded interpretation.

## Run it

Python 3.11 or newer; standard library only.

```bash
python analysis.py
python -m unittest discover -s tests -v
python -m http.server 8000
```

The first run downloads the public 5.3 MB CMS file into `data/raw/`. A checksum mismatch stops the run for review. It exports a full local `outputs/drug_years.csv`, smaller cohort results, findings, and dashboard data. The raw file and full local CSV are ignored by Git; reproduce them with the command above. Visit `http://localhost:8000/dashboard/`.

## Interpret carefully

The source excludes products with fewer than 11 claims in the latest year and can redact earlier cells. Missing history remains missing. Historical totals cover the products listed in this release. A fill is not a standardized course of treatment; average spending per fill reflects supply and product mix. Beneficiaries overlap across products. The bridge is an arithmetic explanation, not a causal estimate of price, treatment value, or real-world savings.

[Read the findings](outputs/findings.md) for numerical results and questions worth investigating next.
