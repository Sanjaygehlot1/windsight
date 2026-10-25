# WindSight

**Wind Generation Forecast & Accuracy Analysis for UK Day-Ahead Electricity Procurement**

WindSight is a web application developed for a UK electricity utility's procurement team. It helps users understand the wind generation forecasts available when making day-ahead electricity purchasing decisions and evaluate their accuracy against actual generation.

The application analyzes national-level wind generation data for purchasing decisions made between **1–31 January 2026**, using Elexon's FUELHH and WINDFOR datasets.

## Features

**1. Wind Generation Forecasts**
- View forecasts available before a selected purchasing decision cutoff.
- Select a decision date and view the following day's forecast.
- Compare forecasted and actual wind generation through interactive charts.
- Examine half-hourly observations and forecast publication times.
- Export daily analysis as CSV.

**2. Forecast Accuracy Analysis**
- Evaluate forecast performance using MAE, RMSE, bias, and P90 absolute error.
- Analyze daily and monthly forecasting errors.
- Identify overestimation and underestimation of wind generation.
- View matched data coverage and daily accuracy breakdowns.
- Export monthly analysis as CSV.

**3. Data Reliability**
- Uses actual Elexon wind generation records.
- Selects only forecasts published before or at the decision cutoff.
- Preserves missing observations rather than estimating values.
- Uses a saved historical dataset for reproducible results.

## Tech Stack

| Technology | Purpose |
|---|---|
| React + Vite | Frontend |
| Python + FastAPI | Backend and data analysis |
| Recharts | Data visualization |
| Elexon API | Wind generation data |
| Docker | Application deployment |
| Pytest | Backend testing |

## Project Structure

```text
windsight/
├── backend/
│   ├── app/
│   │   ├── main.py          # API endpoints and data loading
│   │   ├── elexon.py        # Elexon API integration
│   │   └── analytics.py     # Forecast selection and accuracy calculations
│   ├── data/                # Historical Elexon data snapshot
│   ├── scripts/             # Data retrieval utilities
│   ├── tests/               # Backend tests
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── main.jsx         # React application
│   │   └── style.css        # Application styling
│   └── package.json         # Frontend dependencies
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## How to Run

### Using Docker (Recommended)

Make sure Docker is installed and running.

Clone the repository:

```bash
git clone https://github.com/Sanjaygehlot1/windsight
cd windsight
```

Start the application:

```bash
docker compose up --build
```

Open the application at:

**http://localhost:5173**

To stop the application:

```bash
docker compose down
```

### Run Backend Tests

```bash
pip install -r backend/requirements.txt
python -m pytest -q
```

## Data Sources and Methodology

WindSight uses two Elexon datasets:

- [FUELHH](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream) — Actual generation records filtered to `fuelType = WIND`.
- [WINDFOR](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream) — Wind generation forecasts and publication timestamps.

For each delivery period, the backend selects the latest forecast published before or at the selected decision cutoff and compares it with actual generation at the same timestamp.

Forecast errors are calculated using matched observations only.

The retrieved forecast data is hourly, while actual generation is half-hourly. Therefore, exact timestamp matching produces approximately 50% coverage. Missing forecast values are not estimated.

The default 12:00 UK decision cutoff is a configurable assumption for this pilot.

## Project Links

- **Live Application:** [Live Link](https://windsight-blond.vercel.app/)
- **GitHub Repository:** [Github Repo](https://github.com/Sanjaygehlot1/windsight)
- **Demo Video:** [Unlisted YouTube Video](https://youtu.be/WaWwya93qLQ)

## AI Assistance

OpenAI ChatGPT/Codex was used to assist with code development, debugging, testing, and documentation.

## Notes

- The project focuses exclusively on January 2026 purchasing decisions, corresponding to delivery dates from 2 January to 1 February 2026.
- Only the specified Elexon wind generation datasets are used.
- WindSight supports procurement analysis but does not calculate actual electricity purchase quantities, since demand and existing supply information are outside the project scope.
