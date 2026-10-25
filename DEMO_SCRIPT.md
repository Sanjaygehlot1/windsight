# Demo recording guide (maximum 10 minutes)

> Do not claim that Elexon data, production performance, or a live deployment was verified unless you have independently verified it. Record while the deployed app is successfully showing real January 2026 Elexon data.

## Part 1 — Client pitch (0:00–4:50)

**0:00–0:40 — Why WindSight**
"Day-ahead procurement needs a reliable picture of tomorrow's wind supply. Our pilot focuses on one risk: acting on a forecast that wasn't available at decision time, or failing to understand its historical error. WindSight joins wind forecast and actual data from Elexon into a decision-time-safe view."

**0:40–1:50 — What the team knew at cutoff**
Show the date and configurable previous-day UK cutoff, then the forecast-versus-actual chart. Explain why later updates are excluded even if more accurate. Describe MW and the distinction between forecast and actual.

**1:50–3:00 — Quantified forecast uncertainty**
Show MAE, RMSE, bias and coverage. Explain positive bias means wind was overforecast. Open Forecast Accuracy and point out daily error variation, p90 absolute error, and data availability. Never present p90 as a guaranteed upper bound.

**3:00–4:10 — How this helps a buying decision**
Discuss shortfall exposure and the need for a buffer; clarify the product is an input to procurement judgement, not a complete buy recommendation without demand, contracted generation, and price/market information. Export the 30-minute CSV.

**4:10–4:50 — Pilot value / next steps**
Summarise time-safe traceability, objective backtesting and visible data gaps. Propose operationalising ingestion and validating a client-specific cutoff; then adding approved utility positions and demand feeds as a separate phase.

## Part 2 — Technical review (4:50–9:50)

**4:50–5:35 — Architecture**
React/Vite client → FastAPI `/api/dashboard` → Elexon dataset streams → point-in-time analytics → chart and CSV. Docker Compose runs the two services.

**5:35–6:45 — Ingestion and temporal logic**
Open `backend/app/elexon.py` and `analytics.py`. Explain daily request chunks, timezone-aware parsing, `fuelType == WIND`, and `max(publishTime)` among forecasts published before the configured cutoff for each startTime. Highlight test that rejects the later, more accurate forecast.

**6:45–7:40 — Accuracy and quality**
Show metrics formulas, 30-minute MW-to-MWh conversion, matched-only denominators, coverage, and missingness handling. Discuss equal timestamp joins and exact source fields.

**7:40–8:35 — UI and API**
Show FastAPI route and response shape, React day selector, cutoff setting, charts, descriptive uncertainty panel and CSV export. Explain error handling and refresh.

**8:35–9:15 — Practices and limitations**
Run `pytest -q`; show `docker compose up --build`. Call out live integration validation, no database/auth yet, sample-only January, no artificially generated data, and why metrics aren't a calibrated prediction interval.

**9:15–9:50 — Knowledge transfer**
Highlight README, architecture and suggested next priorities: persistent data snapshots, retry/backoff, monitoring, larger holdout evaluation and client-specific decision cutoff.

## Submission checklist

- [ ] Connect to Elexon from a real deployment and verify all January 2026 source dates and completeness.
- [ ] Confirm stream endpoint date query semantics, including `publishTime` and historical revisions; adjust ingestion if needed.
- [ ] Run backend tests, frontend production build, and Docker smoke test.
- [ ] Deploy a functioning public HTTPS React + FastAPI application to Vercel/Heroku or a supported hosting combination.
- [ ] Create a public GitHub repo with an anonymous random repo name, commit code, and update README with verified deployment URL.
- [ ] Record both sections, maximum 10 minutes combined, upload YouTube as *unlisted*.
- [ ] Open GitHub, live application and unlisted YouTube URLs in an incognito/private browser window and verify access.
- [ ] Complete https://forms.cloud.microsoft/r/FTX6K2bbnU with those verified URLs.
