import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BarChart,
  Bar,
  CartesianGrid,
  LineChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Cell,
} from "recharts";
import {
  Wind,
  PanelLeftClose,
  PanelLeftOpen,
  ChartNoAxesCombined,
  BarChart3,
  ArrowUpRight,
  Download,
  RefreshCw,
  CalendarDays,
  Clock3,
  Check,
  AlertCircle,
  Info,
  ChevronLeft,
  ChevronRight,
  Database,
  ArrowRight,
} from "lucide-react";
import "./style.css";

const API = import.meta.env.VITE_API_URL || "";
const NAV = [
  { id: "forecasts", title: "Forecasts", icon: ChartNoAxesCombined },
  { id: "accuracy", title: "Accuracy", icon: BarChart3 },
];
const number = (v, decimals = 1) =>
  v == null
    ? "—"
    : Number(v).toLocaleString("en-GB", { maximumFractionDigits: decimals });
const dateText = (value) =>
  new Date(`${value}T12:00:00Z`).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "Europe/London",
  });
const nextDay = (value) => {
  const d = new Date(`${value}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
};
const timeText = (value) =>
  value
    ? new Date(value).toLocaleTimeString("en-GB", {
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Europe/London",
      })
    : "—";
const timestamp = (value) =>
  value
    ? new Date(value).toLocaleString("en-GB", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Europe/London",
      })
    : "—";
function Button({
  children,
  icon: Icon,
  secondary = false,
  className = "",
  ...props
}) {
  return (
    <button
      className={`button ${secondary ? "secondary" : ""} ${className}`}
      {...props}
    >
      {Icon && <Icon size={15} />}
      {children}
    </button>
  );
}
function Panel({ title, description, action, children, className = "" }) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-heading">
        <div>
          <h2>{title}</h2>
          {description && <p>{description}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
function Metric({
  label,
  value,
  unit = "MW",
  detail,
  icon: Icon = ChartNoAxesCombined,
}) {
  return (
    <div className="metric">
      <div className="metric-label">
        {label}
        <Icon size={17} />
      </div>
      <div className="metric-value">
        {number(value)}
        {value != null && <span>{unit}</span>}
      </div>
      <p>{detail}</p>
    </div>
  );
}
function ChartTooltip({ active, payload, label, daily = false }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <b>{daily ? dateText(label) : `${timeText(label)} UK`}</b>
      {payload.map((p) => (
        <div key={p.dataKey}>
          <i style={{ background: p.color }} />
          <span>{p.name}</span>
          <strong>{number(p.value)} MW</strong>
        </div>
      ))}
    </div>
  );
}
function GenerationChart({ points, showActual }) {
  const available = points.some(
    (p) => p.forecastMW != null || (showActual && p.actualMW != null),
  );
  if (!available)
    return (
      <div className="empty-chart">
        <Database size={25} />
        <h3>No eligible observations</h3>
        <p>
          There is no forecast for this delivery day at the selected cutoff. Try
          a later decision time.
        </p>
      </div>
    );
  return (
    <div className="generation-chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={points}
          margin={{ top: 15, right: 15, left: 0, bottom: 12 }}
        >
          <CartesianGrid stroke="#e5e9df" vertical={false} />
          <XAxis
            dataKey="startTime"
            ticks={points
              .filter((_, index) => index % 6 === 0)
              .map((p) => p.startTime)}
            tickFormatter={timeText}
            minTickGap={38}
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 11, fill: "#77847a" }}
            dy={10}
          />
          <YAxis
            width={62}
            tickFormatter={(v) => number(v, 0)}
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 11, fill: "#77847a" }}
          />
          <Tooltip content={<ChartTooltip />} />
          <Line
            name="Forecast at cutoff"
            dataKey="forecastMW"
            stroke="#264d3d"
            strokeWidth={2.7}
            dot={{ r: 2.8, fill: "#264d3d", strokeWidth: 0 }}
            activeDot={{ r: 5 }}
            connectNulls={false}
          />
          {showActual && (
            <Line
              name="Actual generation"
              dataKey="actualMW"
              stroke="#bd684d"
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={false}
              activeDot={{ r: 4 }}
              connectNulls={false}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
function Methodology() {
  return (
    <details className="methodology">
      <summary>
        <Info size={16} /> How the comparison works{" "}
        <span>Sources, assumptions & definitions</span>
      </summary>
      <div className="method-body">
        <div>
          <h3>Only the forecast known at decision time</h3>
          <p>
            For each delivery half-hour, select the WINDFOR record with the
            latest <code>publishTime</code> at or before the selected cutoff on
            the previous UK calendar day. Later updates are excluded.
          </p>
          <p>
            12:00 UK is a configurable pilot assumption, not a claimed exchange
            deadline. January decisions (1–31 Jan) correspond to deliveries from
            2 Jan to 1 Feb 2026.
          </p>
        </div>
        <div>
          <h3>Matched data, transparent errors</h3>
          <p>
            Error = forecast − actual. Positive error means wind generation was
            overestimated. MAE is the average absolute error; RMSE gives more
            weight to larger misses; bias measures average signed error.
          </p>
          <p>
            P90 is the historical 90th percentile of absolute errors, not a
            guaranteed future limit. Missing values are excluded, never replaced
            with zero. January metrics are retrospective, not information
            available to an earlier January decision.
          </p>
        </div>
        <div>
          <h3>Two sources. No extra assumptions.</h3>
          <p>
            <a
              href="https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream"
              target="_blank"
              rel="noreferrer"
            >
              FUELHH · WIND actuals <ArrowUpRight size={12} />
            </a>
            <br />
            <a
              href="https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream"
              target="_blank"
              rel="noreferrer"
            >
              WINDFOR · wind forecasts <ArrowUpRight size={12} />
            </a>
          </p>
          <p>
            National Elexon wind generation in MW. Actuals are half-hourly;
            forecasts retain their native source timestamps. Actuals are
            retrospective outturns. Demand, prices and utility positions are
            outside this pilot, so it does not calculate how much electricity to
            buy.
          </p>
        </div>
      </div>
    </details>
  );
}
function EvidenceTable({ points }) {
  const [page, setPage] = useState(0);
  useEffect(() => setPage(0), [points]);
  const pages = Math.ceil(points.length / 8);
  return (
    <Panel
      title="Half-hourly observations"
      description="Trace every selected forecast back to its publication time. All times are UK time."
    >
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Delivery time</th>
              <th>Forecast (MW)</th>
              <th>Actual (MW)</th>
              <th>Error (MW)</th>
              <th>Forecast published</th>
            </tr>
          </thead>
          <tbody>
            {points.slice(page * 8, page * 8 + 8).map((p) => (
              <tr key={p.startTime}>
                <td>{timeText(p.startTime)}</td>
                <td>{number(p.forecastMW)}</td>
                <td>{number(p.actualMW)}</td>
                <td className={p.errorMW > 0 ? "positive-error" : ""}>
                  {p.errorMW > 0 ? "+" : ""}
                  {number(p.errorMW)}
                </td>
                <td className="muted">{timestamp(p.publishTime)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="table-footer">
        <span>
          {page * 8 + 1}–{Math.min((page + 1) * 8, points.length)} of{" "}
          {points.length} half-hours · Positive error = overforecast
        </span>
        <div>
          <button
            aria-label="Previous observations"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
          >
            <ChevronLeft size={16} />
          </button>
          <span>
            {page + 1} / {pages || 1}
          </span>
          <button
            aria-label="Next observations"
            disabled={page >= pages - 1}
            onClick={() => setPage((p) => p + 1)}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </Panel>
  );
}
function App() {
  const [view, setView] = useState(
    location.hash === "#accuracy" ? "accuracy" : "forecasts",
  );
  const [collapsed, setCollapsed] = useState(() => {
    try {
      const saved = localStorage.getItem("windsight-sidebar");
      return saved
        ? saved === "collapsed"
        : window.matchMedia("(max-width: 700px)").matches;
    } catch {
      return false;
    }
  });
  const [decision, setDecision] = useState("2026-01-14");
  const [cutoff, setCutoff] = useState("12:00");
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [showActual, setShowActual] = useState(true);
  const [toast, setToast] = useState("");
  const delivery = nextDay(decision);
  const [hour, minute] = cutoff.split(":").map(Number);
  useEffect(() => {
    const listener = () =>
      setView(location.hash === "#accuracy" ? "accuracy" : "forecasts");
    window.addEventListener("hashchange", listener);
    return () => window.removeEventListener("hashchange", listener);
  }, []);
  useEffect(() => {
    try {
      localStorage.setItem(
        "windsight-sidebar",
        collapsed ? "collapsed" : "expanded",
      );
    } catch {}
  }, [collapsed]);
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setBusy(true);
    setError("");
    setData(null);
    const timeout = setTimeout(() => controller.abort(), 240000);
    fetch(`${API}/api/dashboard?cutoff_hour=${hour}&cutoff_minute=${minute}`, {
      signal: controller.signal,
    })
      .then(async (r) => {
        if (!r.ok) {
          let message = "Elexon data could not be loaded. Please retry.";
          try {
            message = (await r.json()).detail || message;
          } catch {}
          throw new Error(
            typeof message === "string"
              ? message
              : "Invalid request. Please check the decision cutoff.",
          );
        }
        return r.json();
      })
      .then((result) => {
        if (
          !Array.isArray(result.periods) ||
          !Array.isArray(result.daily) ||
          !result.metrics
        )
          throw new Error("The API returned an unexpected response.");
        if (active) setData(result);
      })
      .catch((e) => {
        if (active)
          setError(
            e.name === "AbortError"
              ? "The request timed out. Please check the backend connection and retry."
              : e.message,
          );
      })
      .finally(() => {
        clearTimeout(timeout);
        if (active) setBusy(false);
      });
    return () => {
      active = false;
      clearTimeout(timeout);
      controller.abort();
    };
  }, [hour, minute, refresh]);
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(""), 4000);
    return () => clearTimeout(t);
  }, [toast]);
  const go = (id) => {
    setView(id);
    location.hash = id;
    window.scrollTo(0, 0);
  };
  const points = React.useMemo(
    () => data?.periods.filter((p) => p.deliveryDate === delivery) || [],
    [data, delivery],
  );
  const selected = data?.daily.find((d) => d.date === delivery);
  const metrics = data?.metrics;
  const valid = data && !busy && !error;
  const exportCSV = () => {
    if (!valid) return;
    const rows = view === "accuracy" ? data.periods : points;
    const keys = [
      "decisionDate",
      "deliveryDate",
      "startTime",
      "cutoff",
      "publishTime",
      "forecastMW",
      "actualMW",
      "errorMW",
    ];
    const csv = [
      keys.join(","),
      ...rows.map((p) => keys.map((k) => p[k] ?? "").join(",")),
    ].join("\r\n");
    const url = URL.createObjectURL(
      new Blob([csv], { type: "text/csv;charset=utf-8" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = `windsight-${view === "accuracy" ? "january-decisions" : decision}-cutoff-${cutoff.replace(":", "")}.csv`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setToast(
      "CSV downloaded. Timestamps are UTC; blank values indicate missing data.",
    );
  };
  return (
    <div className={`app ${collapsed ? "is-collapsed" : ""}`}>
      <aside className="sidebar">
        <a
          className="brand"
          href="#forecasts"
          aria-label="WindSight home"
          onClick={() => go("forecasts")}
        >
          <span className="brand-icon">
            <Wind size={24} />
          </span>
          <span className="brand-name">
            WindSight<small>WIND INTELLIGENCE</small>
          </span>
        </a>
        <button
          className="collapse-button"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-expanded={!collapsed}
          onClick={() => setCollapsed((c) => !c)}
        >
          {collapsed ? (
            <PanelLeftOpen size={18} />
          ) : (
            <>
              <PanelLeftClose size={18} />
              <span>Collapse sidebar</span>
            </>
          )}
        </button>
        <div className="nav-caption">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {NAV.map(({ id, title, icon: Icon }) => (
            <button
              key={id}
              onClick={() => go(id)}
              className={view === id ? "active" : ""}
              aria-current={view === id ? "page" : undefined}
              aria-label={title}
              title={collapsed ? title : undefined}
            >
              <Icon size={19} />
              <span>{title}</span>
              {view === id && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <span className="source-icon">
            <Database size={18} />
          </span>
          <div>
            <b>Elexon BMRS</b>
            <p>FUELHH + WINDFOR</p>
            <small>January 2026 pilot</small>
          </div>
        </div>
      </aside>
      <div className="shell">
        <header className="topbar">
          <span>
            Workspace <ChevronRight size={13} />
            <b>{view === "forecasts" ? "Forecasts" : "Accuracy"}</b>
          </span>
          <span className="period-badge">
            <CalendarDays size={13} />
            January 2026 decisions
          </span>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <div className="eyebrow">UK NATIONAL WIND · HISTORICAL PILOT</div>
              <h1>
                {view === "forecasts" ? "Wind forecasts" : "Forecast accuracy"}
              </h1>
              <p>
                {view === "forecasts"
                  ? "See the latest forecast available before a day-ahead buying decision."
                  : "Quantify forecast error across January decisions using matched half-hourly observations."}
              </p>
            </div>
            <Button
              icon={Download}
              secondary
              disabled={!valid}
              onClick={exportCSV}
            >
              Export {view === "accuracy" ? "month" : "day"} CSV
            </Button>
          </div>
          <div className="filters">
            {view === "forecasts" ? (
              <>
                <label>
                  <span>
                    <CalendarDays size={14} />
                    Decision date
                  </span>
                  <select
                    aria-label="Decision date"
                    value={decision}
                    onChange={(e) => setDecision(e.target.value)}
                  >
                    {Array.from({ length: 31 }, (_, i) => {
                      const d = `2026-01-${String(i + 1).padStart(2, "0")}`;
                      return (
                        <option key={d} value={d}>
                          {dateText(d)}
                        </option>
                      );
                    })}
                  </select>
                </label>
                <div className="delivery-indicator">
                  <ArrowRight size={17} />
                  <div>
                    <small>Delivery day</small>
                    <b>{dateText(delivery)}</b>
                  </div>
                </div>
              </>
            ) : (
              <div className="month-summary">
                <CalendarDays size={18} />
                <div>
                  <small>Decision period</small>
                  <b>1–31 January 2026</b>
                  <span>Deliveries: 2 Jan – 1 Feb</span>
                </div>
              </div>
            )}
            <label>
              <span>
                <Clock3 size={14} />
                Decision cutoff · UK time
              </span>
              <input
                aria-label="Decision cutoff"
                type="time"
                step="60"
                value={cutoff}
                onChange={(e) => {
                  if (/^\d{2}:\d{2}$/.test(e.target.value))
                    setCutoff(e.target.value);
                }}
              />
            </label>
            <div className="cutoff-note">
              <Check size={15} />
              <span>
                Only forecasts published
                <br />
                at or before this cutoff
              </span>
            </div>
            <Button
              icon={RefreshCw}
              secondary
              onClick={() => setRefresh((n) => n + 1)}
              disabled={busy}
            >
              Reload data
            </Button>
          </div>
          {busy && (
            <div className="state-panel" role="status">
              <RefreshCw size={25} className="spin" />
              <h2>Loading Elexon observations</h2>
              <p>
                Checking forecast publication times against your decision
                cutoff.
              </p>
            </div>
          )}
          {error && (
            <div className="state-panel error" role="alert">
              <AlertCircle size={28} />
              <div className="state-copy">
                <h2>Data is unavailable</h2>
                <p>{error}</p>
                <p>No sample or generated values are substituted.</p>
              </div>
              <Button onClick={() => setRefresh((n) => n + 1)}>
                Try again
              </Button>
            </div>
          )}
          {valid && (
            <>
              {view === "forecasts" ? (
                <>
                  <div className="section-caption">
                    <span>DELIVERY DAY SNAPSHOT</span>
                    <span>{dateText(delivery)} · 48 half-hours</span>
                  </div>
                  <div className="metrics">
                    <Metric
                      label="Mean forecast"
                      value={selected?.meanForecastMW}
                      detail={`${selected?.forecastPeriods ?? 0} eligible forecast timestamps`}
                    />
                    <Metric
                      label="Mean actual"
                      value={selected?.matchedMeanActualMW}
                      detail="Actuals at matched forecast times"
                    />
                    <Metric
                      label="Day’s forecast MAE"
                      value={selected?.maeMW}
                      detail="Average absolute forecast error"
                      icon={BarChart3}
                    />
                    <Metric
                      label="Matched coverage"
                      value={selected?.coveragePct}
                      unit="%"
                      detail={`${selected?.matchedPeriods ?? 0} / 48 matched half-hours`}
                      icon={Check}
                    />
                  </div>
                  {selected?.matchedPeriods < 48 && (
                    <div className="inline-notice">
                      <Info size={17} />
                      <span>
                        {data.forecastResolutionMinutes === 60
                          ? `Elexon supplies hourly forecasts for this period. ${selected.matchedPeriods} of 48 half-hours match exactly; the other half-hours are not interpolated. Forecasts appear as individual points.`
                          : `${48 - selected.matchedPeriods} half-hours lack a matched forecast or actual. Metrics use available pairs only.`}
                      </span>
                    </div>
                  )}
                  <Panel
                    title="Forecast vs actual generation"
                    description={`Delivery: ${dateText(delivery)} · Forecast known by ${dateText(decision)}, ${cutoff} UK`}
                    action={
                      <label className="toggle-label">
                        <input
                          type="checkbox"
                          checked={showActual}
                          onChange={(e) => setShowActual(e.target.checked)}
                        />
                        <span>Show actuals</span>
                      </label>
                    }
                  >
                    <div className="chart-meta">
                      <span>Generation · MW</span>
                      <div className="legend">
                        <span>
                          <i />
                          Forecast at cutoff
                        </span>
                        {showActual && (
                          <span>
                            <i className="actual" />
                            Actual generation
                          </span>
                        )}
                      </div>
                    </div>
                    <GenerationChart points={points} showActual={showActual} />
                    <div className="chart-footnote">
                      <Info size={14} />
                      Actuals are shown for retrospective comparison. They were
                      not known at the decision cutoff.
                    </div>
                  </Panel>
                  <div className="day-details">
                    <div>
                      <span>Forecast observations</span>
                      <b>
                        {selected?.forecastPeriods ?? 0}{" "}
                        <small>timestamps</small>
                      </b>
                      <p>
                        {data.forecastResolutionMinutes === 60
                          ? "Hourly forecasts as supplied by Elexon"
                          : "Available at the selected cutoff"}
                      </p>
                    </div>
                    <div>
                      <span>Actual observations</span>
                      <b>
                        {selected?.actualPeriods ?? 0} <small>half-hours</small>
                      </b>
                      <p>National wind generation from FUELHH</p>
                    </div>
                    <div>
                      <span>Latest selected publication</span>
                      <b>
                        {timestamp(
                          points
                            .map((p) => p.publishTime)
                            .filter(Boolean)
                            .sort()
                            .at(-1),
                        )}{" "}
                        <small>UK</small>
                      </b>
                      <p>
                        Each target time uses its own latest eligible forecast.
                      </p>
                    </div>
                    <button onClick={() => go("accuracy")}>
                      <BarChart3 size={18} />
                      <span>
                        See January accuracy
                        <small>Put this day’s error in context</small>
                      </span>
                      <ArrowUpRight size={17} />
                    </button>
                  </div>
                  <EvidenceTable points={points} />
                </>
              ) : (
                <>
                  <div className="section-caption">
                    <span>JANUARY DECISION-PERIOD ACCURACY</span>
                    <span>
                      {number(metrics.matchedPeriods, 0)} matched half-hours
                    </span>
                  </div>
                  <div className="metrics">
                    <Metric
                      label="Mean absolute error"
                      value={metrics.maeMW}
                      detail="Typical absolute miss · MAE"
                      icon={BarChart3}
                    />
                    <Metric
                      label="Root mean square error"
                      value={metrics.rmseMW}
                      detail="Emphasises larger misses · RMSE"
                    />
                    <Metric
                      label="Forecast bias"
                      value={metrics.biasMW}
                      detail="Positive = overestimated wind"
                    />
                    <Metric
                      label="P90 absolute error"
                      value={metrics.p90AbsErrorMW}
                      detail="Historical percentile, not a forecast bound"
                    />
                  </div>
                  <Panel
                    title="Daily forecast error"
                    description="Mean absolute error by decision day. Select a bar to inspect the next day’s delivery."
                    action={<span className="small-badge">MAE · MW</span>}
                  >
                    <div className="accuracy-chart">
                      {data.daily.some((d) => d.maeMW != null) ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={data.daily}
                            margin={{ top: 15, right: 10, left: 0, bottom: 10 }}
                          >
                            <CartesianGrid stroke="#eceef1" vertical={false} />
                            <XAxis
                              dataKey="decisionDate"
                              tickFormatter={(d) => d.slice(-2)}
                              axisLine={false}
                              tickLine={false}
                              tick={{ fontSize: 11, fill: "#90959d" }}
                            />
                            <YAxis
                              width={62}
                              tickFormatter={(v) => number(v, 0)}
                              axisLine={false}
                              tickLine={false}
                              tick={{ fontSize: 11, fill: "#90959d" }}
                            />
                            <Tooltip
                              content={<ChartTooltip daily />}
                              cursor={{ fill: "#f3f4f6" }}
                            />
                            <Bar
                              name="Mean absolute error"
                              dataKey="maeMW"
                              fill="#252b32"
                              radius={[4, 4, 0, 0]}
                              maxBarSize={25}
                              onClick={(d) => {
                                setDecision(d.decisionDate);
                                go("forecasts");
                              }}
                              cursor="pointer"
                            >
                              {data.daily.map((d) => (
                                <Cell
                                  key={d.date}
                                  fill={
                                    d.decisionDate === decision
                                      ? "#6a99aa"
                                      : "#252b32"
                                  }
                                />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="empty-chart">
                          <Database size={25} />
                          <h3>No matched data at this cutoff</h3>
                          <p>
                            Try another decision time. Missing observations are
                            not scored as zero error.
                          </p>
                        </div>
                      )}
                    </div>
                    <div className="chart-footnote">
                      Decision day in January 2026 · a missing bar indicates no
                      matched observations.
                    </div>
                  </Panel>
                  {data.forecastResolutionMinutes === 60 && (
                    <div className="inline-notice">
                      <Info size={17} />
                      <span>
                        Source frequency: hourly WINDFOR forecasts and
                        half-hourly FUELHH actuals. With every forecast
                        timestamp matched, coverage of the half-hour grid is
                        50%. This is a source-resolution difference, not 50%
                        missing API responses.
                      </span>
                    </div>
                  )}
                  <div className="accuracy-bottom">
                    <Panel
                      title="Data coverage"
                      description="Accuracy is only as useful as the observations behind it."
                    >
                      <div className="coverage-value">
                        {number(metrics.coveragePct)}
                        <span>% matched</span>
                      </div>
                      <div className="coverage-track">
                        <div
                          style={{
                            width: `${Math.min(100, Math.max(0, metrics.coveragePct))}%`,
                          }}
                        />
                      </div>
                      {[
                        ["Matched half-hours", metrics.matchedPeriods],
                        ["Forecast available", metrics.forecastPeriods],
                        ["Actual available", metrics.actualPeriods],
                      ].map(([label, v]) => (
                        <div className="fact" key={label}>
                          <span>{label}</span>
                          <b>
                            {number(v, 0)} / {number(metrics.totalPeriods, 0)}
                          </b>
                        </div>
                      ))}
                      <p className="footnote">
                        Missing or conflicting observations are excluded from
                        accuracy metrics.
                      </p>
                    </Panel>
                    <Panel
                      title="What the errors mean"
                      description="A focused input to procurement judgement."
                    >
                      <div className="interpretation">
                        <span className="interpretation-icon">
                          <ChartNoAxesCombined size={18} />
                        </span>
                        <div>
                          <h3>
                            Overforecasting leaves less wind than expected
                          </h3>
                          <p>
                            {metrics.biasMW == null
                              ? "No matched data is available at this cutoff."
                              : metrics.biasMW > 0
                                ? `Across matched periods, the forecast exceeded actual wind by ${number(metrics.biasMW)} MW on average.`
                                : metrics.biasMW < 0
                                  ? `Across matched periods, the forecast was below actual wind by ${number(Math.abs(metrics.biasMW))} MW on average.`
                                  : "The mean signed error is zero across matched observations."}
                          </p>
                        </div>
                      </div>
                      <div className="interpretation">
                        <span className="interpretation-icon">
                          <Info size={18} />
                        </span>
                        <div>
                          <h3>Use the size and direction of past errors</h3>
                          <p>
                            MAE describes the average miss. RMSE highlights
                            larger errors. Bias shows direction, while P90
                            summarises the observed error tail.
                          </p>
                          <p>
                            These are retrospective January results, not a
                            calibrated prediction interval or a recommendation
                            for how much power to buy.
                          </p>
                        </div>
                      </div>
                    </Panel>
                  </div>
                  <Panel
                    title="Daily accuracy breakdown"
                    description="Review completeness alongside error, then open a decision day."
                  >
                    <div className="table-scroll daily-table">
                      <table>
                        <thead>
                          <tr>
                            <th>Decision day</th>
                            <th>Delivery day</th>
                            <th>MAE (MW)</th>
                            <th>RMSE (MW)</th>
                            <th>Bias (MW)</th>
                            <th>Matched</th>
                            <th>
                              <span className="sr-only">Open day</span>
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.daily.map((d) => (
                            <tr key={d.date}>
                              <td>{dateText(d.decisionDate)}</td>
                              <td className="muted">{dateText(d.date)}</td>
                              <td>{number(d.maeMW)}</td>
                              <td>{number(d.rmseMW)}</td>
                              <td>{number(d.biasMW)}</td>
                              <td>
                                {d.matchedPeriods} / {d.totalPeriods}
                              </td>
                              <td>
                                <button
                                  className="table-link"
                                  aria-label={`View decision ${d.decisionDate}`}
                                  onClick={() => {
                                    setDecision(d.decisionDate);
                                    go("forecasts");
                                  }}
                                >
                                  View <ArrowUpRight size={13} />
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Panel>
                </>
              )}
              <div className="source-line">
                <span>
                  <span className="status-dot" />
                  Elexon FUELHH (WIND) + WINDFOR
                </span>
                <span>
                  Retrieved {timestamp(data.loadedAt)} UK ·{" "}
                  {data.dataMode === "snapshot"
                    ? "Saved historical snapshot"
                    : "Fetched from Elexon"}
                </span>
              </div>
              {(data.quality?.invalidRowsSkipped > 0 ||
                data.quality?.conflictingPeriodsExcluded > 0) && (
                <p className="quality-note">
                  Data quality: {data.quality.invalidRowsSkipped} invalid rows
                  skipped; {data.quality.conflictingPeriodsExcluded} conflicting
                  observations excluded.
                </p>
              )}
            </>
          )}
          <Methodology />
          <footer>
            <span>WindSight · January 2026 pilot</span>
            <span>Elexon FUELHH · WINDFOR · National wind</span>
          </footer>
        </main>
      </div>
      {toast && (
        <div className="toast" role="status">
          <Check size={16} />
          {toast}
        </div>
      )}
    </div>
  );
}
createRoot(document.getElementById("root")).render(<App />);
