import csv
import json
from pathlib import Path
from typing import Optional, Sequence


def _detect_delimiter(sample: str) -> str:
    """Detect CSV delimiter from a sample line."""
    candidates = [",", ";", "\t", "|", ":"]
    counts = {c: sample.count(c) for c in candidates}
    # Choose the most frequent, default to comma
    return max(counts, key=counts.get) or ","


def convert_csv_to_json(
    input_path: str,
    output_path: Optional[str] = None,
    *,
    encoding: str = "utf-8",
    detect_delimiter: bool = True,
    force_delimiter: Optional[str] = None,
    skip_empty_lines: bool = True,
) -> Path:
    """Convert a CSV file to a JSON file with an array of objects.

    Args:
        input_path: Path to the CSV file.
        output_path: Path to write the JSON file. If None, uses same name with .json.
        encoding: File encoding to read.
        detect_delimiter: If True, auto-detect delimiter from first non-empty line.
        force_delimiter: If set, use this delimiter instead of detection.
        skip_empty_lines: If True, ignore completely empty lines.

    Returns:
        Path to the written JSON file.
    """
    in_path = Path(input_path)
    if output_path is None:
        out_path = in_path.with_suffix(".json")
    else:
        out_path = Path(output_path)

    if not in_path.is_file():
        raise FileNotFoundError(f"Input CSV not found: {in_path}")

    # Read a small sample to detect delimiter if needed
    delimiter = ","
    if force_delimiter is not None:
        delimiter = force_delimiter
    elif detect_delimiter:
        with in_path.open("r", encoding=encoding, newline="") as f:
            for line in f:
                if skip_empty_lines and not line.strip():
                    continue
                delimiter = _detect_delimiter(line)
                break

    rows = []
    with in_path.open("r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            if skip_empty_lines and all(
                (v is None or str(v).strip() == "") for v in row.values()
            ):
                continue
            # Strip whitespace around values
            cleaned = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            rows.append(cleaned)

    with out_path.open("w", encoding="utf-8") as out:
        json.dump(rows, out, ensure_ascii=False, indent=2)

    return out_path


def batch_convert_csv_to_json(
    input_paths: Sequence[str],
    output_dir: Optional[str] = None,
    *,
    encoding: str = "utf-8",
    detect_delimiter: bool = True,
    force_delimiter: Optional[str] = None,
    skip_empty_lines: bool = True,
) -> list[Path]:
    """Batch conversion helper for multiple CSV files."""
    results: list[Path] = []
    for path in input_paths:
        in_path = Path(path)
        if output_dir is None:
            out_path = None
        else:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / (in_path.stem + ".json")
        result = convert_csv_to_json(
            str(in_path),
            str(out_path) if out_path is not None else None,
            encoding=encoding,
            detect_delimiter=detect_delimiter,
            force_delimiter=force_delimiter,
            skip_empty_lines=skip_empty_lines,
        )
        results.append(result)
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert a CSV file to JSON (array of objects)."
    )
    parser.add_argument("input", help="Path to the input CSV file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Path to the output JSON file. Defaults to same name with .json.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Encoding of the CSV file (default: utf-8).",
    )
    parser.add_argument(
        "--delimiter",
        help="Force a specific delimiter (e.g. ',' ';' '\\t'). If not set, auto-detect.",
    )
    parser.add_argument(
        "--no-detect-delimiter",
        action="store_true",
        help="Disable delimiter auto-detection.",
    )
    args = parser.parse_args()

    out_path = convert_csv_to_json(
        args.input,
        args.output,
        encoding=args.encoding,
        detect_delimiter=not args.no_detect_delimiter,
        force_delimiter=args.delimiter,
    )
    print(f"Written: {out_path}")
