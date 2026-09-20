let
    // Public aggregate source. The release URL is fixed; this does not fetch a rolling latest release.
    Source = Csv.Document(
        Web.Contents("https://data.cms.gov", [RelativePath = "sites/default/files/2026-06/98218f98-166c-4723-8438-c344a4ef96a6/DSD_PTD_RY26_P04_V10_DY24_BGM.csv"]),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Overall = Table.SelectRows(Headers, each [Mftr_Name] = "Overall"),
    UniqueCount = Table.RowCount(Table.Distinct(Overall, {"Brnd_Name", "Gnrc_Name"})),
    Checked = if UniqueCount <> Table.RowCount(Overall) then error "Duplicate Overall brand/ingredient keys in source." else Overall,
    Sorted = Table.Sort(Checked, {{"Brnd_Name", Order.Ascending}, {"Gnrc_Name", Order.Ascending}}),
    Indexed = Table.AddIndexColumn(Sorted, "DrugKey", 1, 1, Int64.Type)
in
    Indexed
