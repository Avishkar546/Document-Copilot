# Document Copilot

Starter workspace for a React/TypeScript frontend, a FastAPI/SQLAlchemy backend,
and a SEC EDGAR 10-K downloader.

- Frontend setup and scripts: [frontend/README.md](./frontend/README.md)
- Backend setup, database configuration, and API checks:
  [backend/README.md](./backend/README.md)
- SEC filings download instructions: [data/README.md](./data/README.md)

The downloader stores filings by report year in `data/downloads/`. Generated
filing data and local databases are excluded from Git.
