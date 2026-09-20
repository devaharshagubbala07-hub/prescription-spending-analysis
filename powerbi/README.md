# Prescription spending in Power BI

A native Power BI Desktop project using the same public CMS release as the Python/SQL analysis. Three report pages cover spending concentration, annual growth and its arithmetic components, and definitions with source checks. Developed with AI assistance.

**Status:** project-file schemas, model references, layout coordinates, and source controls have been checked. **Power BI Desktop refresh, DAX execution, and visual rendering still need to be verified in Desktop.** A prepared project is not a claim that those native-engine checks have passed.

## Open the report

1. Download the [Power BI package](https://raw.githubusercontent.com/devaharshagubbala07-hub/prescription-spending-analysis/main/downloads/PrescriptionSpending_PowerBI.zip) and extract the whole ZIP to a short local folder, such as `C:\Portfolio`. Alternatively, on the [repository home page](https://github.com/devaharshagubbala07-hub/prescription-spending-analysis), choose **Code → Download ZIP**. Keep the report and semantic-model folders together.
2. Use a current version of **Power BI Desktop**. Under **File → Options and settings → Options → Preview features**, enable **Power BI Project (.pbip) save option** and **Store reports using enhanced metadata format (PBIR)** if those options are present and not already enabled. Restart Desktop if prompted. This project uses a TMSL model; it does not require enabling TMDL authoring.
3. Open **`powerbi/PrescriptionSpending.pbip`**. You can also use **File → Open → Browse** and select that file. Do not open only one copied JSON file.
4. Select **Home → Refresh**. The report imports the pinned 5.3 MB CSV directly from `https://data.cms.gov`. If a source-credentials prompt appears, choose **Anonymous** for that public CMS source; if asked for the privacy level, choose **Public**. No personal file path or API key is required. Blank cards before the first refresh are expected because the project has no cached data.
5. Check **01 Spending overview** with **Year = 2024** and **Drug group = GLP-1 / GIP**. Expect gross spending of **$27.51B**, **21.83M** fills, average spending per fill of **$1,260.12**, and **9.5%** of listed spending. Clear the drug-group selection to see all listed products; `Other listed products` is the complementary group, not the all-products total.
6. Check **02 Growth & drivers** with **Year = 2024**, **Product = Ozempic (Semaglutide)**. Both history charts retain the five-year context. The bridge should reconcile to the spending change, with a zero residual to the nearest cent. Select **Liraglutide (Liraglutide)** to check missing history, and **Wegovy (Semaglutide)** to see the 142-fill prior-year baseline note.
7. In **DAX query view**, open the included **Release checks** query and run it. If it does not appear as a tab automatically, open [validation/desktop_checks.dax](validation/desktop_checks.dax), paste it into a new DAX query tab, and run it. All nine checks should return `TRUE` after a successful refresh.
8. Save the project. If you want a single-file copy, use **File → Save As** and choose **Power BI Desktop file (.pbix)**. Creating that PBIX and capturing authentic report screenshots are Desktop steps.

If Desktop reports a file, formula, or refresh error, preserve the exact message and filename. Do not present the report as validated until the relevant check succeeds. The existing web dashboard continues to work independently of this Power BI project.

## Report design

| Page | What to examine | Controls |
|---|---|---|
| 01 Spending overview | Gross spending, fills, weighted average, share of all listed spending, leading products, historical context | Year; drug group. The history chart intentionally ignores the year slicer. |
| 02 Growth & drivers | Spending, fill, and average-per-fill growth; two history charts; volume-first bridge; small-baseline context | One year; one product. The history charts intentionally ignore the year slicer. |
| 03 Definitions & checks | Model structure, source limitations, release counts, independent 2024 reference totals | Release checks ignore the analytical slicers. |

The leading-products chart shows the first ten **dense ranks**; ties can include more than ten products. The fixed reference note on the overview page describes the GLP-1 / GIP cohort in 2024. Dynamic cards and charts respond to their documented filters.

## Inspect the work

- [Model diagram and data dictionary](MODEL.md)
- [DAX measures and interpretation](DAX_MEASURES.md)
- [Source controls](validation/source_controls.json)
- [Power Query import and transformations](queries)
- [Native Desktop checks](validation/desktop_checks.dax)
- [Original CMS source manifest](../source.json)

The report imports public aggregates, not Merative or patient records. June 2026 is the **release date**; observations end in **2024**. Spending is gross, before rebates. A fill is not a standardized dose or treatment course.

## Rebuild the project definitions

`python powerbi/build_project.py` regenerates the model and report metadata from `queries/*.pq`, `measures.json`, and the builder's layout. It uses the Python standard library. **Regeneration overwrites generated definitions**; preserve any changes you make in Desktop before running the builder. It does not run Power Query, evaluate DAX, or render Power BI visuals.

Microsoft references: [Desktop projects](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview), [PBIR reports](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report), and [semantic-model files](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset). The bundled Microsoft base theme retains its [license and attribution](THIRD_PARTY_NOTICES.md).
