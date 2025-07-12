#!/usr/bin/env python
"""
Command-line interface.

Examples
--------
python -m pubmed_paper_fetcher "breast cancer AND antibody therapy"
python -m pubmed_paper_fetcher -d -f results.csv "CRISPR AND gene editing"
"""
from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional

from rich import print as rprint

from .fetcher import fetch_papers, save_or_print


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="get-papers-list",
        description=(
            "Fetch PubMed papers that include at least one pharma/biotech author "
            "and output them as CSV."
        ),
    )
    p.add_argument("query", help="PubMed query (quote it if it contains spaces)")
    p.add_argument(
        "-f",
        "--file",
        metavar="CSV_FILE",
        help="Save results to this CSV file instead of printing",
    )
    p.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Print debug information during execution",
    )
    p.add_argument(
        "-l", "--limit", type=int, default=1000,
        help="Max PubMed IDs to fetch (default 1000)",
    )
    return p


def main(argv: Optional[list[str]] = None) -> None:  # noqa: D401
    """Parse CLI args and run fetch."""
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    rprint(f":mag_right:  [bold]Query:[/bold] {args.query}")

    try:
        df = fetch_papers(args.query, retmax=args.limit, debug=args.debug)
    except Exception as exc:
        rprint(f"[red]❌ Error:[/red] {exc}")
        sys.exit(1)

    save_or_print(df, args.file)


if __name__ == "__main__":
    main()
