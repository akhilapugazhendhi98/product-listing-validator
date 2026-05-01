# Product Listing Validator

## Overview

Product Listing Validator is a reusable AI skill for a coding assistant. It validates ecommerce product listing CSV files before they are uploaded to a store or inventory system. The skill checks that all required fields are present and complete, enforces product-specific size rules, validates price format and range, checks SKU format, flags duplicate SKUs, and produces a catalog readiness report.

A SKU — Stock Keeping Unit — is a unique product identifier used to track individual product variations such as size or color. Duplicate or missing SKUs are a common source of catalog errors.

For this project, I used WearPawsitive-style apparel listings as the sample rule set. The skill itself is not limited to apparel; the same validation pattern can be adapted to other ecommerce categories by changing the catalog rules.

## Why I Chose This Skill

Ecommerce sellers often build product listing files by hand — in spreadsheets or exported CSVs — before uploading them to a storefront. A single mistake in a required field, an unsupported size value, or a duplicated SKU can affect upload readiness, customer-facing product pages, and fulfillment accuracy. These are not edge cases — they are the kinds of errors that happen regularly in manual catalog workflows.

This is a narrow, well-defined task with clear pass/fail rules, which makes it a good fit for a reusable AI skill. The assistant can understand what the user is asking for and guide the workflow, but the exact validation — parsing rows, checking field values, enforcing size rules, counting errors — needs to be handled by a script that produces consistent and verifiable results. The combination of an AI assistant for orchestration and a deterministic script for validation is what makes the skill reliable and repeatable across different sellers and catalog files.

## Why the Script Is Load-Bearing

The Python script `validate_listings.py` does the deterministic work that a language model should not guess at or approximate. Specifically, the script:

- Parses the CSV file using Python's standard `csv` module
- Validates that all required columns are present in the header
- Checks every row for blank required fields
- Enforces product-specific size rules (e.g. bandanas only accept L or XL; socks only accept One Size)
- Validates that prices are numeric, positive, and within a reasonable range
- Checks that SKUs follow a consistent uppercase hyphenated format
- Detects duplicate SKUs across the entire file
- Counts total errors and warnings
- Prints a structured Markdown validation report to stdout

The AI assistant orchestrates the workflow — confirming the file path, referencing the catalog rules, and summarizing results for the user — but the script performs the exact validation. This separation keeps the results accurate and repeatable regardless of how the question is phrased.

## Skill Structure

~~~text
product-listing-validator/
├── .agents/
│   └── skills/
│       └── product-listing-validator/
│           ├── SKILL.md
│           ├── scripts/
│           │   └── validate_listings.py
│           ├── references/
│           │   └── catalog_rules.md
│           └── assets/
├── samples/
│   ├── valid_listings.csv
│   ├── invalid_listings.csv
│   └── caution_listings.csv
├── README.md
└── requirements.txt
~~~

- `SKILL.md` — defines when and how to use the skill, validation rules, script usage, and limitations
- `validate_listings.py` — the Python validation script; standard library only, no external dependencies
- `catalog_rules.md` — reference document for allowed fields, product types, sizes, and severity definitions
- `samples/` — three test CSV files covering a clean case, an error case, and a caution case

## How to Use It

Run the validator from the project root by passing a CSV file path as the argument. The same script is used for every test case — only the file path at the end of the command changes.

**Normal case — clean file:**

~~~bash
python3 .agents/skills/product-listing-validator/scripts/validate_listings.py samples/valid_listings.csv
~~~

**Edge/error case — file with blocking errors:**

~~~bash
python3 .agents/skills/product-listing-validator/scripts/validate_listings.py samples/invalid_listings.csv
~~~

**Cautious/limited case — file with warnings only:**

~~~bash
python3 .agents/skills/product-listing-validator/scripts/validate_listings.py samples/caution_listings.csv
~~~

The script exits with code `0` if there are no errors, `1` if errors are found, and `2` if the file path is invalid or the file cannot be read.

## Sample Test Results

| Test Case | File | Result | Purpose |
|---|---|---|---|
| Normal case | `valid_listings.csv` | PASS — 0 errors, 0 warnings | Confirms the skill does not create false positives on clean data |
| Edge/error case | `invalid_listings.csv` | FAIL — 12 errors, 0 warnings | Confirms the skill catches blocking catalog problems |
| Cautious/limited case | `caution_listings.csv` | PASS — 0 errors, 2 warnings | Confirms the skill flags suspicious values without rewriting listings or making subjective marketing judgments |

## What Worked Well

The skill produced consistent, accurate validation results across all three test cases. It correctly passed clean data without false positives, caught every category of blocking error in the error case (missing fields, bad prices, invalid sizes, and duplicate SKUs), and handled the caution case by raising price warnings without crossing into listing rewrites or marketing advice. The skill stayed within its defined scope throughout all three tests.

Separating the deterministic validation work into a standalone Python script made the results reliable and easy to verify — the output was identical whether the script was run directly from the terminal or invoked through the skill workflow.

## Limitations

- Validates local CSV files only. The skill does not fetch or push data from any remote source.
- Does not connect to Shopify, Etsy, Square, or any other storefront or inventory API.
- Does not rewrite, rephrase, or improve product listings in any way.
- Does not evaluate whether a product description is persuasive, complete, or marketing-effective.
- Does not manage inventory counts, pricing strategy, or order fulfillment.
- Only supports the product types and size rules explicitly defined in `catalog_rules.md`. Unsupported product types are flagged as errors rather than guessed.

## Demo Video

Video walkthrough: ADD VIDEO LINK HERE
