# Anomaly Detection

The anomaly engine (`backend/app/anomaly.py`) runs three complementary
algorithms every 60 seconds. All detection is server-side — the ESP32 performs
no anomaly logic. No ML models are used; detection is purely statistical.

---

## 1. Static Threshold Violations

Checks the most recent reading (within the last 5 minutes) for each
device+metric against hardcoded bounds.

| Metric | Limit | Severity |
|---|---|---|
| Temperature | > 40 C | critical |
| Humidity | > 85% | warning |
| Voltage | > 16.5V | critical |
| Current | > 5.0A | critical |

Good for catching clear-cut dangerous conditions (overheating, overcurrent).

---

## 2. Z-Score Detection

Detects sudden spikes or drops relative to recent behavior, even when the
reading is within absolute thresholds.

- **Window**: 24 hours of historical data
- **Threshold**: Z-score >= 3.0 (3 standard deviations from the mean)
- **Min samples**: 30 readings required for a reliable baseline
- **Severity**: warning

**How it works**: For each device+metric, the engine computes the mean and
standard deviation over the last 24 hours. It then calculates
`Z = |latest_value - mean| / stddev`. A Z-score of 3+ means the reading is
statistically unusual for that sensor's recent behavior.

**Example**: If voltage averages 14.5V with stddev 0.2V over 24h, a reading
of 15.3V gives Z = (15.3 - 14.5) / 0.2 = 4.0 — flagged as an anomaly, even
though 15.3V is well within the 16.5V absolute threshold.

---

## 3. Long-Term Drift Detection

Catches gradual degradation that happens too slowly for Z-score to flag —
the key algorithm for detecting solar panel efficiency loss.

- **Baseline**: Average over days 8-37 (30-day window, excluding the recent period)
- **Recent**: Average over the last 7 days
- **Threshold**: Drift > 2x the historical standard deviation
- **Min samples**: 100 readings per period
- **Severity**: info
- **Rate limit**: Max 1 alert per device+metric per 24 hours

**How it works**: Compares the recent 7-day average against a 30-day
historical baseline. If the shift exceeds twice the historical standard
deviation, a drift alert is raised.

**Example — panel degradation**: If voltage averaged 15.5V (stddev 0.3V) over
the historical period but has dropped to 14.2V over the last 7 days, the
drift is 1.3V. The threshold is 2 x 0.3 = 0.6V. Since 1.3 > 0.6, a drift
alert fires — indicating possible panel soiling, wiring degradation, or
battery issues.

---

## Alert Rate Limiting

To prevent alert spam, each algorithm checks for recent duplicates before
inserting:

| Algorithm | Cooldown |
|---|---|
| Threshold | 30 minutes per device+metric |
| Z-score | 30 minutes per device+metric |
| Drift | 24 hours per device+metric |

---

## Alert Lifecycle

1. Anomaly engine inserts an alert with severity, type, value, and threshold.
2. Alert appears in the dashboard's Alerts panel (auto-refreshes every 10s).
3. User acknowledges the alert via `POST /api/alerts/{id}/acknowledge`.
4. Acknowledged alerts are hidden from the default view but retained in the database.
