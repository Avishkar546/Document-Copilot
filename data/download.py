"""Download recent company 10-K filings from SEC EDGAR.

Set SEC_USER_AGENT to a descriptive application name and contact email before
running this script, as required by the SEC's fair-access policy.
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import request

TICKERS = ("AAPL", "MSFT", "NVDA", "AMZN", "GOOGL")
FILINGS_PER_COMPANY = 5
OUTPUT_DIR = Path(__file__).resolve().parent / "downloads"
REQUEST_DELAY_SECONDS = 0.12
USER_AGENT = "Document Copilot gaikwadavishkar546@gmail.com"

COMPANY_CIKS = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "NVDA": "0001045810",
    "AMZN": "0001018724",
    "GOOGL": "0001652044",
}


def get_bytes(url: str, accept: str) -> bytes:
    if not USER_AGENT:
        raise RuntimeError(
            "Set SEC_USER_AGENT to an application name and contact email "
            "before downloading filings."
        )
    req = request.Request(
        url,
        headers={"Accept": accept, "User-Agent": USER_AGENT},
    )
    with request.urlopen(req, timeout=60) as response:
        content = response.read()
    time.sleep(REQUEST_DELAY_SECONDS)
    return content


def get_json(url: str) -> dict[str, Any]:
    content = get_bytes(url, "application/json")
    result: Any = json.loads(content.decode("utf-8"))
    if not isinstance(result, dict):
        raise ValueError(f"Expected a JSON object from SEC: {url}")
    return result


def extract_10k_filings(
    submission: dict[str, Any], target_years: set[str]
) -> list[dict[str, str]]:
    filings_data = submission.get("filings", {})
    recent = filings_data.get("recent", submission)
    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    documents = recent.get("primaryDocument", [])
    filing_dates = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])
    filings: list[dict[str, str]] = []

    for form, accession, document, filing_date, report_date in zip(
        forms,
        accessions,
        documents,
        filing_dates,
        report_dates,
        strict=True,
    ):
        year = (report_date or filing_date)[:4]
        if form == "10-K" and year in target_years:
            filings.append(
                {
                    "year": year,
                    "form": form,
                    "accession_number": accession,
                    "primary_document": document,
                    "filing_date": filing_date,
                    "report_date": report_date,
                }
            )
    return filings


def download_filings() -> dict[str, Any]:
    if not USER_AGENT:
        raise RuntimeError(
            "Set SEC_USER_AGENT to an application name and contact email "
            "before downloading filings."
        )

    current_year = datetime.now(UTC).year
    target_years = {
        str(year) for year in range(current_year - FILINGS_PER_COMPANY, current_year)
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "source": "SEC EDGAR",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "form": "10-K",
        "downloaded_count": 0,
        "filings": [],
    }

    for ticker, cik in COMPANY_CIKS.items():
        print(f"Downloading {ticker} filings...")
        submission = get_json(f"https://data.sec.gov/submissions/CIK{cik}.json")
        filings = extract_10k_filings(submission, target_years)
        for archive in submission.get("filings", {}).get("files", []):
            if len(filings) >= FILINGS_PER_COMPANY:
                break
            historical = get_json(f"https://data.sec.gov/submissions/{archive['name']}")
            filings.extend(extract_10k_filings(historical, target_years))

        for filing in filings[:FILINGS_PER_COMPANY]:
            accession_path = filing["accession_number"].replace("-", "")
            source_url = (
                "https://www.sec.gov/Archives/edgar/data/"
                f"{int(cik)}/{accession_path}/{filing['primary_document']}"
            )
            year_dir = OUTPUT_DIR / filing["year"]
            year_dir.mkdir(parents=True, exist_ok=True)
            local_path = year_dir / (
                f"{ticker.lower()}_{filing['form'].lower()}_"
                f"{filing['filing_date']}_{filing['accession_number']}"
                f"{Path(filing['primary_document']).suffix or '.html'}"
            )
            local_path.write_bytes(
                get_bytes(
                    source_url,
                    "text/html,application/xhtml+xml,application/xml",
                )
            )
            manifest["filings"].append(
                {
                    "ticker": ticker,
                    "cik": cik,
                    "form": filing["form"],
                    "filing_date": filing["filing_date"],
                    "report_date": filing["report_date"],
                    "accession_number": filing["accession_number"],
                    "primary_document": filing["primary_document"],
                    "source_url": source_url,
                    "local_path": str(local_path.relative_to(OUTPUT_DIR)),
                }
            )
            manifest["downloaded_count"] += 1

    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


if __name__ == "__main__":
    result = download_filings()
    print(f"Downloaded {result['downloaded_count']} filing(s) to {OUTPUT_DIR}")
    print(f"Manifest: {OUTPUT_DIR / 'manifest.json'}")
