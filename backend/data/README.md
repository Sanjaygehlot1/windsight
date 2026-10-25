# Real Elexon pilot snapshot

`january-2026.json.gz` was fetched from the two required public Elexon dataset streams on **2026-10-25 at 07:15 UTC**. The exact retrieval timestamp is inside the file and in every API response.

- 1,488 FUELHH WIND records for delivery dates 2026-01-02 through 2026-02-01, queried using settlement dates and `fuelType=WIND`.
- 19,856 distinct WINDFOR source rows from publication windows 2025-12-29 through 2026-01-31. These include forecast revisions and delivery targets beyond the pilot; analytics selects only the required delivery targets and eligible publications.
- Fields retained: `startTime`, `publishTime`, `generation`, plus actual `fuelType`.
- Duplicate boundary rows are removed. No timestamps are interpolated, generation is not altered, and no synthetic rows are inserted.
- Forecast target timestamps in this snapshot are hourly. Actuals are half-hourly.

Reproduce from `backend/` using `python -m scripts.fetch_snapshot` with the installed requirements and internet access. A later source fetch can contain revised actuals; the retrieval time distinguishes that dataset. Restart the API or rebuild its container to load an updated file.

Sources:
- https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream
- https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream
