# WindSight — UK day-ahead wind intelligence

**Pilot period:** 1–31 January 2026 (delivery dates). React, FastAPI, Docker.

## Problem / value proposition
UK power procurement teams must make day-ahead decisions before wind generation is known. WindSight shows the latest *available at decision-time* wind forecast alongside eventual FUELHH wind outturn and quantified historical forecast error. It does not claim to calculate net procurement volume: demand, supply contracts and prices are explicitly out of scope.

## Start locally

Prerequisites: Docker + Compose; working outbound internet access to `https://data.elexon.co.uk`.

```bash
docker compose up --build
```

- UI: http://localhost:5173
- Backend API: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

The initial January download can take time: Elexon data is requested as daily intervals and retained in process memory until refresh/restart. An upstream data fetch failure is displayed as an error, **never** replaced with fictional figures.

Run tests without Docker (from the `backend/` directory):

```bash
pip install -r requirements.txt
pytest -q
```

## Files

```text
backend/
  app/main.py          FastAPI routes, CORS, memory cache
  app/elexon.py        Elexon BMRS client and daily chunked retrieval
  app/analytics.py     Temporal join, cutoff logic, metrics
  tests/test_analytics.py  Unit tests for leakage, missing data, wind filtering
  requirements.txt    Python dependencies
  Dockerfile          Backend container
frontend/
  src/main.jsx        Dashboard, day/cutoff filters, charts, CSV export
  src/style.css       Responsive dashboard design
  index.html          HTML entry
  vite.config.js      Development proxy
  package.json        Node scripts and dependencies
  Dockerfile          Frontend container
docker-compose.yml    Run frontend + backend
.gitignore            Local generated file exclusions
README.md             Guide and design review
```

## Data contract

Only the specified source streams are used:
- `GET /bmrs/api/v1/datasets/FUELHH/stream` — restrict to `fuelType = WIND`, `startTime`, `generation`.
- `GET /bmrs/api/v1/datasets/WINDFOR/stream` — `startTime`, `publishTime`, `generation`.

Both are queried in one-day windows across **29 Dec 2025 – 2 Feb 2026** to include forecasts published prior to January delivery periods. Deliveries are filtered to **1–31 January 2026**. The stream endpoint's date-filter semantics and historical completeness must be validated against Elexon in the deployed environment before client sign-off. Production ingestion should also deduplicate by Elexon record identity and store immutable ingestion snapshots.

All source instants are parsed as UTC timestamps. The forecast cutoff for each *delivery date* is the previous calendar day at a configurable hour in `Europe/London` (default **12:00**); it is an **assumption**, not an asserted market-wide exchange gate closure. For each delivery `startTime`, select the forecast record having the highest `publishTime <= cutoff`. Never use a later forecast even if it predicts the same delivery half-hour. A published forecast may be missing for an interval; this is reported as missing, not zero.

### Metrics

For matched half-hour periods only, error `e = forecast MW - actual MW`.
- MAE = mean(|e|)
- RMSE = sqrt(mean(e²))
- Bias = mean(e), positive meaning wind overforecast / potential shortage
- p90 absolute error = empirical 90th percentile of |e|
- Coverage = matched periods / total expected delivery periods
- MWh for each half-hour = MW × 0.5, summed separately for forecast and actual

The p90 absolute error is **retrospective descriptive uncertainty**, not a statistically calibrated predictive interval. January is an in-sample descriptive retrospective; for predictive confidence or procurement recommendations, evaluate on separate dates and incorporate demand/positions/market costs (outside assignment scope).

## Design decisions and limitations

1. **No look-ahead leakage:** publishTime controls point-in-time eligibility.
2. **Clearly distinct reliability and completeness:** missing data excluded from metrics and counted in coverage.
3. **Request observability:** source and loaded timestamp visible; the UI exposes manual refresh and CSV export.
4. **No fake live data:** API/network errors are exposed to the user.
5. **Deliberately small MVP:** no database, authentication, background scheduler, demand feeds or price integrations.
6. **Scalability path:** scheduled ingestion + persisted raw records (Postgres), retry/backoff, quality checks, forecast provenance, configurable cutoff by exchange gate, auth, monitoring, multi-month holdout evaluation.

**Important unverified integration point:** The Elexon host was not reachable from the development sandbox, so the entire-month retrieval and stream query parameter behavior could not be end-to-end verified here. Test with live access; adjust API filtering according to Elexon's current docs if required. This is a working prototype, not a production-certified data pipeline.

## Hosting / deployment

**Live deployment URL:** Not yet deployed (replace with a verified public URL after deploying). Neither a Vercel nor a Heroku deployment has been performed. The Python API must be reachable over HTTPS in addition to the React UI. When separately hosting the frontend and API, set `VITE_API_URL` at frontend *build time* and `CORS_ORIGINS` on the backend to the exact public frontend origin. Deploying only the React assets does **not** deploy the FastAPI API.

## AI usage disclosure

**AI tools used:** OpenAI ChatGPT was used to research the domain, propose the architecture, and generate initial React, Python, test, Docker and documentation code. All outputs require human review and external integration validation before operational use.

## Source documentation

- https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream
- https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream
- https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind/latest/stream
