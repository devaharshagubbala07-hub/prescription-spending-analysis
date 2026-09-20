# Explain the analysis

This new portfolio project was built with AI assistance. Reproduce it, inspect the queries, and make a change you can explain before presenting it as evidence of your own understanding.

1. **Start with the question.** Which products concentrate spending, and why did a selected product's gross spending change?
2. **State what the data represents.** CMS release June 2026; observations through 2024; Medicare Part D; gross spending before rebates.
3. **Show the double-counting trap.** Compare an Overall row with its manufacturer detail. Explain why summing both is wrong.
4. **Show a missing observation.** Inspect Mounjaro or a recently appearing product. Missing historical data is not proof of zero use.
5. **Read the SQL.** Explain why an aggregate average is total dollars divided by total fills, rather than the mean of product averages.
6. **Explain the Ozempic bridge.** Fill counts can rise while average spending per fill falls. Explain the decomposition order and why this is not a causal price analysis.
7. **Close with a decision and its limits.** Prioritize a budget review. Identify the employer-level data, rebates, and days-supply detail you would need before forecasting an employer's costs.

Practice change: add a separate, explicitly labeled insulin-combination cohort. Re-run the pipeline and compare its inclusion rules without changing the published single-agent cohort silently.
