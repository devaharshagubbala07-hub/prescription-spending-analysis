let
    Source = #"CMS Overall",
    ParseNumber = (value as any) as nullable number =>
        if value = null or Text.Trim(Text.From(value)) = "" then null
        else Number.FromText(Text.From(value), "en-US"),
    Rows = List.Combine(List.Transform(Table.ToRecords(Source), (r as record) =>
        List.Transform({2020..2024}, (y as number) =>
            let
                Spend = ParseNumber(Record.Field(r, "Tot_Spndng_" & Text.From(y))),
                Claims = ParseNumber(Record.Field(r, "Tot_Clms_" & Text.From(y)))
            in [DrugKey = r[DrugKey], Year = y,
                SpendingCents = if Spend = null then null else Int64.From(Number.Round(Spend * 100, 0, RoundingMode.AwayFromZero)),
                Fills = Claims]
        )
    )),
    Long = Table.FromRecords(Rows),
    Available = Table.SelectRows(Long, each [SpendingCents] <> null),
    Invalid = Table.SelectRows(Available, each [SpendingCents] < 0 or [Fills] = null or [Fills] <= 0 or Number.Mod([Fills], 1) <> 0),
    Checked = if Table.RowCount(Invalid) > 0 then error "Invalid spending or prescription-fill denominator." else Available,
    Typed = Table.TransformColumnTypes(Checked, {{"DrugKey", Int64.Type}, {"Year", Int64.Type}, {"SpendingCents", Int64.Type}, {"Fills", Int64.Type}}, "en-US")
in
    Typed
