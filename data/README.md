# SEC filings

`download.py` downloads up to five recent annual 10-K filings for Apple,
Microsoft, NVIDIA, Amazon, and Alphabet (Google) from SEC EDGAR. Filings are
stored under `downloads/<report year>/`, with a `manifest.json` describing the
downloaded records. The script never clears existing downloads.

The SEC requires a descriptive `User-Agent` with contact information. Set
`SEC_USER_AGENT` before running the downloader:

```powershell
$env:SEC_USER_AGENT = "Document Copilot contact@example.com"
python data\download.py
```

Replace the example contact with a monitored email address. The download folder
is excluded from Git; the manifest and filing documents are generated when the
script runs.
