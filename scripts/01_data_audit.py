"""
Data audit: enumerates every raw source file this pipeline consumes and its
shape, so a future run can quickly tell if an upstream file changed shape.
Mirrors the audit step of the FIFA World Cup pipeline this project pairs with.
"""
import pandas as pd
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT = Path(__file__).resolve().parents[1] / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

rows = []
for p in sorted(RAW.rglob("*")):
    if p.is_dir() or p.name.startswith("."):
        continue
    try:
        if p.suffix.lower() == ".csv":
            df = pd.read_csv(p, low_memory=False, on_bad_lines="skip")
            rows.append({"file": str(p.relative_to(RAW)), "rows": len(df), "cols": len(df.columns)})
        elif p.suffix.lower() == ".xlsx":
            xls = pd.ExcelFile(p)
            for sheet in xls.sheet_names:
                df = xls.parse(sheet)
                rows.append({"file": f"{p.relative_to(RAW)} [{sheet}]", "rows": len(df), "cols": len(df.columns)})
    except Exception as e:
        rows.append({"file": str(p.relative_to(RAW)), "rows": -1, "cols": -1, "error": str(e)})

pd.DataFrame(rows).to_csv(OUT / "data_audit_summary.csv", index=False)
print(f"Audited {len(rows)} sheets/files -> {OUT / 'data_audit_summary.csv'}")
