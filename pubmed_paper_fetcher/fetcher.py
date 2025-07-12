"""
fetcher.py
~~~~~~~~~~
Low-level helpers to:
• run PubMed ESearch / EFetch
• parse XML
• flag non-academic (pharma/biotech) authors
• return a pandas DataFrame
"""

from __future__ import annotations

import csv
import logging
import re
import textwrap
from datetime import datetime
from io import StringIO
from typing import Dict, List

import pandas as pd
import requests
from lxml import etree
from rich.progress import track

# --------------------------------------------------------------------------- #
# Constants & simple heuristics
# --------------------------------------------------------------------------- #

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
USER_AGENT = "pubmed-paper-fetcher/0.1 (https://github.com/your/repo)"
BATCH_SIZE = 200  # EFetch limit is 300; 200 keeps us safe

COMPANY_KEYWORDS = re.compile(
    r"""
    pharm|biotech|inc\.?|ltd\.?|llc|gmbh|corp|corporation|
    s\.?a\.?|plc|k\.?k\.?|co\.?\s?ltd
    """,
    re.I | re.X,
)
ACADEMIC_KEYWORDS = re.compile(
    r"""
    univ|universit|college|academy|school|hospital|centre|center|
    institut|facult|dept|department
    """,
    re.I | re.X,
)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# --------------------------------------------------------------------------- #
# PubMed helpers
# --------------------------------------------------------------------------- #


def esearch(query: str, retmax: int = 1000) -> List[str]:
    """Return a list of PubMed IDs for the query (up to retmax)."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": str(retmax),
    }
    logging.debug("ESearch params: %s", params)
    resp = requests.get(
        f"{NCBI_BASE}/esearch.fcgi",
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    resp.raise_for_status()
    ids = resp.json()["esearchresult"]["idlist"]
    logging.info("ESearch returned %s IDs", len(ids))
    return ids


def efetch(pmids: List[str]) -> List[str]:
    """Yield XML strings for batches of PMIDs."""
    for start in track(range(0, len(pmids), BATCH_SIZE), description="Downloading"):
        batch = pmids[start : start + BATCH_SIZE]
        params = {"db": "pubmed", "id": ",".join(batch), "retmode": "xml"}
        resp = requests.get(
            f"{NCBI_BASE}/efetch.fcgi",
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=60,
        )
        resp.raise_for_status()
        yield resp.text


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #


def is_company_affil(affil: str) -> bool:
    """True if affiliation looks like a company, false if academic."""
    affil_lc = affil.lower()
    return bool(COMPANY_KEYWORDS.search(affil_lc)) and not ACADEMIC_KEYWORDS.search(
        affil_lc
    )


def first_email(text: str) -> str | None:
    """Extract first email address from text, if any."""
    m = EMAIL_RE.search(text)
    return m.group(0) if m else None


def parse_articles(xml_chunk: str) -> List[Dict[str, str]]:
    """Parse an XML chunk (many articles) and return rows for DataFrame."""
    rows: List[Dict[str, str]] = []
    root = etree.fromstring(xml_chunk.encode())

    for art in root.findall(".//PubmedArticle"):
        pmid = art.findtext(".//PMID")
        title = art.findtext(".//ArticleTitle") or "N/A"

        # Publication date (many variants in PubMed)
        pub_date = "N/A"
        date_node = art.find(".//ArticleDate")
        if date_node is None:
            date_node = art.find(".//Journal/JournalIssue/PubDate")

        if date_node is not None:
            y = date_node.findtext("Year") or ""
            m = date_node.findtext("Month") or ""
            d = date_node.findtext("Day") or ""
            pub_date = "-".join([p for p in [y, m, d] if p]) or "N/A"

        non_acad_authors, company_affils = [], []
        corr_email: str | None = None

        for author in art.findall(".//Author"):
            last = author.findtext("LastName") or ""
            first = author.findtext("ForeName") or author.findtext("Initials") or ""
            name = f"{first} {last}".strip()

            for affil_info in author.findall(".//AffiliationInfo"):
                affil = (affil_info.findtext("Affiliation") or "").strip()

                # Email
                if not corr_email:
                    corr_email = first_email(affil)

                # Company?
                if affil and is_company_affil(affil):
                    non_acad_authors.append(name)
                    company_affils.append(affil)

        if non_acad_authors:
            rows.append(
                {
                    "PubmedID": pmid,
                    "Title": textwrap.shorten(title, width=200),
                    "Publication Date": pub_date,
                    "Non-academic Author(s)": "; ".join(sorted(set(non_acad_authors))),
                    "Company Affiliation(s)": "; ".join(sorted(set(company_affils))),
                    "Corresponding Author Email": corr_email or "N/A",
                }
            )
    return rows


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def fetch_papers(query: str, retmax: int = 1000, debug: bool = False) -> pd.DataFrame:
    """Return DataFrame of papers that have ≥1 company author."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    pmids = esearch(query, retmax=retmax)
    rows: List[Dict[str, str]] = []
    for xml in efetch(pmids):
        rows.extend(parse_articles(xml))

    df = pd.DataFrame(
        rows,
        columns=[
            "PubmedID",
            "Title",
            "Publication Date",
            "Non-academic Author(s)",
            "Company Affiliation(s)",
            "Corresponding Author Email",
        ],
    )
    logging.info("Found %s papers with non-academic authors", len(df))
    return df


def save_or_print(df: pd.DataFrame, filename: str | None) -> None:
    """Save DataFrame to CSV or print to console."""
    if filename:
        df.to_csv(filename, index=False)
        print(f"✅ Saved {len(df)} rows to {filename}")
    else:
        if df.empty:
            print("⚠️  No matching papers found.")
        else:
            buf = StringIO()
            df.to_csv(buf, index=False)
            print(buf.getvalue())
