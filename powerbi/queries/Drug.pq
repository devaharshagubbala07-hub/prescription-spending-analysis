let
    Source = #"CMS Overall",
    Fields = Table.SelectColumns(Source, {"DrugKey", "Brnd_Name", "Gnrc_Name"}),
    Names = Table.RenameColumns(Fields, {{"Brnd_Name", "Brand"}, {"Gnrc_Name", "Ingredient"}}),
    Product = Table.AddColumn(Names, "Product", each [Brand] & " (" & [Ingredient] & ")", type text),
    Ingredients = {"semaglutide", "tirzepatide", "dulaglutide", "liraglutide", "exenatide", "exenatide microspheres", "lixisenatide"},
    Group = Table.AddColumn(Product, "Drug group", each if List.Contains(Ingredients, Text.Lower([Ingredient])) then "GLP-1 / GIP" else "Other listed products", type text),
    Typed = Table.TransformColumnTypes(Group, {{"DrugKey", Int64.Type}, {"Brand", type text}, {"Ingredient", type text}}, "en-US")
in
    Typed
