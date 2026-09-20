let
    Source = Table.FromList({2020..2024}, Splitter.SplitByNothing(), {"Year"}),
    Typed = Table.TransformColumnTypes(Source, {{"Year", Int64.Type}}, "en-US")
in
    Typed
