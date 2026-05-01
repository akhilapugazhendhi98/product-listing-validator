# Catalog Rules Reference

This document defines the validation rules applied by the `product-listing-validator` skill. Use this as a reference when interpreting validation output or extending the validator with new product types.

---

## Required Fields

All six fields below must be present and non-blank for every row in the CSV.

| Field | Required | Notes |
|---|---|---|
| `product_name` | Yes | Must not be blank |
| `product_type` | Yes | Must match a supported type (see below) |
| `sku` | Yes | Must not be blank; must be unique across the file |
| `price` | Yes | Must be numeric and greater than zero |
| `size` | Yes | Must match allowed values for the product type |
| `description` | Yes | Must not be blank |

---

## Supported Product Types

Only the following product types are recognized. Any other value in the `product_type` field is flagged as an error.

| Product Type | Notes |
|---|---|
| `tee` | T-shirts |
| `hoodie` | Hooded sweatshirts |
| `bandana` | Pet or fashion bandanas |
| `socks` | Crew or ankle socks |

---

## Allowed Sizes by Product Type

Size values are case-sensitive and must match the allowed values exactly.

| Product Type | Allowed Sizes |
|---|---|
| `tee` | `S`, `M`, `L`, `XL`, `XXL` |
| `hoodie` | `S`, `M`, `L`, `XL`, `XXL` |
| `bandana` | `L`, `XL` |
| `socks` | `One Size` |

Any size value outside these allowed sets — including alternate casing such as `one size` or `xl` — is flagged.

---

## Price Validation Rules

| Rule | Severity |
|---|---|
| Price field must not be blank | ERROR |
| Price must be a valid number (integer or decimal) | ERROR |
| Price must be greater than zero | ERROR |
| Price is unusually low (e.g., under $1.00) | WARNING |
| Price is unusually high (e.g., over $500.00) | WARNING |

---

## SKU Validation Rules

| Rule | Severity |
|---|---|
| SKU field must not be blank | ERROR |
| SKU must be unique across all rows in the file | ERROR |
| SKU should use uppercase letters, numbers, and hyphens only | WARNING |
| SKU should follow a consistent hyphenated format (e.g., `PREFIX-TYPE-###`) | WARNING |

---

## Severity Definitions

| Severity | Meaning | Effect on Upload |
|---|---|---|
| `ERROR` | The listing violates a required rule and cannot be uploaded as-is. | Blocks upload — must be corrected. |
| `WARNING` | The listing may cause display or quality issues but is not strictly invalid. | Does not block upload — review recommended. |

---

## Notes for Extending Rules

- When adding a new product type, define its allowed sizes here before updating the validator script.
- New required fields should be added to both this document and `validate_listings.py`.
- Severity assignments should follow the definitions above: use `ERROR` for data that will break catalog ingestion and `WARNING` for data that may cause downstream quality issues.
