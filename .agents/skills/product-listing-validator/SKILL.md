---
name: product-listing-validator
description: Validates small ecommerce product listing CSV files before catalog upload by checking required fields, product-specific size rules, price format, duplicate SKUs, and catalog readiness. Use when the user asks to inspect, audit, or validate product listing files.
---

# Product Listing Validator

## When to Use This Skill

Use this skill when a user wants to validate a product listing CSV file before uploading it to an ecommerce store or inventory system. This includes auditing listings for missing required fields, unsupported product types, invalid sizes, malformed or negative prices, duplicate SKUs, and general catalog readiness. It is well-suited as a pre-upload quality check during catalog preparation workflows.

## When Not to Use This Skill

Do not use this skill to rewrite or improve product listings, upload products to any storefront, connect to or sync with ecommerce APIs, manage inventory levels, process orders, or evaluate whether a product description is persuasive or marketing-effective. This skill only reads and validates — it never modifies the source file.

## Expected Inputs

The expected input is a local CSV file with the following columns:

| Column | Description |
|---|---|
| `product_name` | Display name of the product |
| `product_type` | Category of the product (see supported types below) |
| `sku` | Unique stock-keeping unit identifier |
| `price` | Numeric selling price |
| `size` | Product size (allowed values vary by product type) |
| `description` | Short product description for the storefront |

**Supported product types:**

| Type | Description |
|---|---|
| `tee` | T-shirts |
| `hoodie` | Hooded sweatshirts |
| `bandana` | Pet or fashion bandanas |
| `socks` | Crew or ankle socks |

## Validation Rules

The following rules are applied to every row in the file:

- **Required fields:** `product_name`, `product_type`, `sku`, `price`, `size`, and `description` must not be blank.
- **Supported product types:** `product_type` must be one of the four supported values. Unsupported types are flagged as errors — size rules are never guessed.
- **Tee sizes:** Must be one of `S`, `M`, `L`, `XL`, or `XXL`.
- **Hoodie sizes:** Must be one of `S`, `M`, `L`, `XL`, or `XXL`.
- **Bandana sizes:** Must be `L` or `XL` only.
- **Socks sizes:** Must be exactly `One Size`. Alternate casing (e.g., `one size`) is flagged.
- **Price format:** Must be a valid positive number. Blank, non-numeric, zero, or negative values are errors.
- **Duplicate SKUs:** Any SKU appearing more than once in the file is flagged as an error.
- **SKU format:** SKUs should use uppercase letters, numbers, and hyphens only (e.g., `BRAND-TYPE-001`). Deviations are flagged as warnings.

For the full rule reference and severity definitions, see `references/catalog_rules.md`.

## Step-by-Step Instructions

1. Confirm the user has provided a valid path to a local CSV file before proceeding.
2. Read `references/catalog_rules.md` if clarification on any rule or severity level is needed.
3. Run `scripts/validate_listings.py` against the provided CSV file path.
4. Treat the script output as the authoritative source of truth for all validation results.
5. Present the results clearly using the output format described below.
6. Do not invent missing product data, silently correct issues, or modify the source file in any way.

## Script Usage

Run the validator from the project root:

```bash
python3 .agents/skills/product-listing-validator/scripts/validate_listings.py samples/valid_listings.csv
```

Replace `samples/valid_listings.csv` with the path to the file you want to validate.

## Expected Output Format

Every validation run must produce a report with the following structure:

**Summary block:**
- Total products checked
- Total errors
- Total warnings
- Pass/fail status (`PASS` if errors = 0, `FAIL` otherwise)

**Issue list** (when issues exist):
- Row number
- Field name
- Severity (`ERROR` or `WARNING`)
- Plain-language explanation of the issue

**Example — clean file:**

```
Validation Report
=================
Total products checked: 13
Errors:                 0
Warnings:               0
Status:                 PASS

No issues found.
```

**Example — file with issues:**

```
Validation Report
=================
Total products checked: 12
Errors:                 8
Warnings:               0
Status:                 FAIL

Row 1  | product_name | ERROR   | Required field is blank.
Row 4  | price        | ERROR   | Price must be numeric and positive. Got: "abc"
Row 6  | size         | ERROR   | Invalid size "S" for product type "bandana". Allowed: L, XL
Row 10 | sku          | ERROR   | Duplicate SKU detected: WP-TEE-DUP-001 (also appears on row 11)
Row 11 | sku          | ERROR   | Duplicate SKU detected: WP-TEE-DUP-001 (also appears on row 10)
```

Issues should be presented in row order. If multiple issues exist on the same row, list each on its own line.

## Important Limitations

- This skill validates **local CSV files only**. It does not fetch, pull, or push data from any remote source.
- This skill does **not** connect to Shopify, Etsy, Square, or any other ecommerce storefront or API.
- This skill does **not** rewrite, rephrase, or improve product descriptions.
- This skill does **not** evaluate whether a description is persuasive, compelling, or marketing-effective.
- This skill does **not** manage inventory counts, pricing strategies, or order fulfillment.
- Unsupported product types are always flagged as errors. The skill never assumes or guesses size rules for unknown types.
