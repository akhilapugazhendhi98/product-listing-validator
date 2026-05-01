"""
validate_listings.py
Product Listing Validator — product-listing-validator skill

Parses a product listing CSV file, validates each row against fixed catalog
rules, and prints a Markdown validation report to stdout.

Usage:
    python3 .agents/skills/product-listing-validator/scripts/validate_listings.py <path/to/file.csv>

Exit codes:
    0 — validation passed (no errors; warnings may be present)
    1 — validation failed (one or more errors found)
    2 — script usage error (bad arguments, file not found, etc.)
"""

import csv
import os
import re
import sys

# ---------------------------------------------------------------------------
# Catalog rules
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = ["product_name", "product_type", "sku", "price", "size", "description"]

SUPPORTED_PRODUCT_TYPES = {"tee", "hoodie", "bandana", "socks"}

ALLOWED_SIZES = {
    "tee":     {"S", "M", "L", "XL", "XXL"},
    "hoodie":  {"S", "M", "L", "XL", "XXL"},
    "bandana": {"L", "XL"},
    "socks":   {"One Size"},
}

PRICE_LOW_THRESHOLD  = 1.00
PRICE_HIGH_THRESHOLD = 500.00

SKU_FORMAT_PATTERN = re.compile(r"^[A-Z0-9]+(-[A-Z0-9]+)*$")

DESCRIPTION_MIN_LENGTH = 20


# ---------------------------------------------------------------------------
# Issue dataclass-style container
# ---------------------------------------------------------------------------

class Issue:
    """Represents a single validation issue on a specific row."""

    def __init__(self, row_num, product_name, field, severity, message):
        self.row_num      = row_num       # 1-based data row number (excludes header)
        self.product_name = product_name  # may be empty if product_name itself is missing
        self.field        = field
        self.severity     = severity      # "ERROR" or "WARNING"
        self.message      = message


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_headers(fieldnames):
    """
    Check that all required columns exist in the CSV header.
    Returns a list of Issue objects (row_num = 0 signals a header-level error).
    """
    issues = []
    if fieldnames is None:
        issues.append(Issue(0, "", "header", "ERROR", "CSV file is empty or has no header row."))
        return issues

    normalised = [f.strip().lower() for f in fieldnames]
    for col in REQUIRED_COLUMNS:
        if col not in normalised:
            issues.append(Issue(
                0, "", "header", "ERROR",
                f'Required column "{col}" is missing from the CSV header.'
            ))
    return issues


def validate_row(row_num, row):
    """
    Validate a single data row against all catalog rules.
    Returns a list of Issue objects for this row.
    """
    issues = []

    # Normalise keys so leading/trailing whitespace in headers doesn't break lookups
    row = {k.strip().lower(): v.strip() for k, v in row.items()}

    product_name = row.get("product_name", "")
    product_type = row.get("product_type", "")
    sku          = row.get("sku", "")
    price_raw    = row.get("price", "")
    size         = row.get("size", "")
    description  = row.get("description", "")

    def add(field, severity, message):
        issues.append(Issue(row_num, product_name, field, severity, message))

    # --- Required field blanks ---
    for field_name, value in [
        ("product_name", product_name),
        ("product_type", product_type),
        ("sku",          sku),
        ("price",        price_raw),
        ("size",         size),
        ("description",  description),
    ]:
        if not value:
            add(field_name, "ERROR", "Required field is blank.")

    # --- Product type ---
    if product_type and product_type not in SUPPORTED_PRODUCT_TYPES:
        add("product_type", "ERROR",
            f'Unsupported product type "{product_type}". '
            f'Allowed: {", ".join(sorted(SUPPORTED_PRODUCT_TYPES))}.')

    # --- Size (only checked when product_type is known and size is present) ---
    if product_type and size and product_type in ALLOWED_SIZES:
        allowed = ALLOWED_SIZES[product_type]
        if size not in allowed:
            add("size", "ERROR",
                f'Invalid size "{size}" for product type "{product_type}". '
                f'Allowed: {", ".join(sorted(allowed))}.')

    # --- Price ---
    if price_raw:
        try:
            price = float(price_raw)
            if price <= 0:
                add("price", "ERROR",
                    f'Price must be a positive number. Got: "{price_raw}".')
            elif price < PRICE_LOW_THRESHOLD:
                add("price", "WARNING",
                    f'Price ${price:.2f} is unusually low (under ${PRICE_LOW_THRESHOLD:.2f}). '
                    f'Verify this is not a data entry error.')
            elif price > PRICE_HIGH_THRESHOLD:
                add("price", "WARNING",
                    f'Price ${price:.2f} is unusually high (over ${PRICE_HIGH_THRESHOLD:.2f}). '
                    f'Verify this is intentional.')
        except ValueError:
            add("price", "ERROR",
                f'Price must be numeric. Got: "{price_raw}".')

    # --- SKU format ---
    if sku and not SKU_FORMAT_PATTERN.match(sku):
        add("sku", "WARNING",
            f'SKU "{sku}" does not follow the expected uppercase hyphenated format '
            f'(e.g., BRAND-TYPE-001).')

    # --- Description length ---
    if description and len(description) < DESCRIPTION_MIN_LENGTH:
        add("description", "WARNING",
            f'Description is very short ({len(description)} characters). '
            f'Consider expanding it to at least {DESCRIPTION_MIN_LENGTH} characters.')

    return issues


def find_duplicate_skus(rows):
    """
    Scan all data rows and return a dict mapping each duplicate SKU to the list
    of 1-based row numbers on which it appears.
    """
    sku_rows = {}
    for row_num, row in rows:
        sku = row.get("sku", "").strip()
        if sku:
            sku_rows.setdefault(sku, []).append((row_num, row))

    duplicates = {sku: entries for sku, entries in sku_rows.items() if len(entries) > 1}
    return duplicates


def build_duplicate_sku_issues(duplicates):
    """
    Convert the duplicate-SKU map into a flat list of Issue objects,
    one per occurrence of the duplicated SKU.
    """
    issues = []
    for sku, entries in duplicates.items():
        row_numbers = [str(rn) for rn, _ in entries]
        other_rows_str = ", ".join(row_numbers)
        for row_num, row in entries:
            row = {k.strip().lower(): v.strip() for k, v in row.items()}
            product_name = row.get("product_name", "")
            issues.append(Issue(
                row_num, product_name, "sku", "ERROR",
                f'Duplicate SKU "{sku}" detected. '
                f'Appears on rows: {other_rows_str}.'
            ))
    return issues


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def render_report(filepath, all_issues, total_rows):
    """
    Render the validation results as a Markdown report and return it as a string.
    """
    errors   = [i for i in all_issues if i.severity == "ERROR"]
    warnings = [i for i in all_issues if i.severity == "WARNING"]
    status   = "PASS" if not errors else "FAIL"

    lines = []
    lines.append("# Product Listing Validation Report")
    lines.append("")
    lines.append(f"**File:** `{filepath}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Total products checked | {total_rows} |")
    lines.append(f"| Total errors           | {len(errors)} |")
    lines.append(f"| Total warnings         | {len(warnings)} |")
    lines.append(f"| Status                 | **{status}** |")
    lines.append("")

    lines.append("## Issues")
    lines.append("")

    if not all_issues:
        lines.append("No issues found.")
    else:
        lines.append("| Row | Product Name | Field | Severity | Issue |")
        lines.append("|---|---|---|---|---|")

        # Sort by row number, then severity (ERRORs before WARNINGs), then field
        severity_order = {"ERROR": 0, "WARNING": 1}
        sorted_issues = sorted(
            all_issues,
            key=lambda i: (i.row_num, severity_order.get(i.severity, 9), i.field)
        )

        for issue in sorted_issues:
            row_label     = str(issue.row_num) if issue.row_num > 0 else "header"
            product_label = issue.product_name if issue.product_name else "—"
            lines.append(
                f"| {row_label} | {product_label} | `{issue.field}` "
                f"| {issue.severity} | {issue.message} |"
            )

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# File reading
# ---------------------------------------------------------------------------

def read_csv(filepath):
    """
    Open and parse the CSV file. Returns (fieldnames, rows) where rows is a
    list of (row_num, dict) tuples. Raises SystemExit on file-level errors.
    """
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(2)

    if not filepath.lower().endswith(".csv"):
        print(f"Error: File does not appear to be a CSV file: {filepath}", file=sys.stderr)
        sys.exit(2)

    rows = []
    fieldnames = None

    try:
        with open(filepath, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            fieldnames = reader.fieldnames
            for row_num, row in enumerate(reader, start=1):
                rows.append((row_num, dict(row)))
    except OSError as exc:
        print(f"Error reading file: {exc}", file=sys.stderr)
        sys.exit(2)

    return fieldnames, rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python3 validate_listings.py <path/to/listings.csv>",
            file=sys.stderr
        )
        sys.exit(2)

    filepath = sys.argv[1]

    # Read file
    fieldnames, rows = read_csv(filepath)

    all_issues = []

    # Header validation — if headers are broken, no point validating rows
    header_issues = validate_headers(fieldnames)
    all_issues.extend(header_issues)

    if not any(i.severity == "ERROR" for i in header_issues):
        # Row-level validation
        for row_num, row in rows:
            all_issues.extend(validate_row(row_num, row))

        # Duplicate SKU check (requires seeing all rows first)
        duplicates = find_duplicate_skus(rows)
        all_issues.extend(build_duplicate_sku_issues(duplicates))

    # Render and print the report
    report = render_report(filepath, all_issues, len(rows))
    print(report)

    # Exit with code 1 if any errors exist
    has_errors = any(i.severity == "ERROR" for i in all_issues)
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
