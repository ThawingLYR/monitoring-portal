# Netatmo data source

Collects observations from public [Netatmo](https://www.netatmo.com/) personal
weather stations around Longyearbyen through the `getpublicdata` API.

> Contributed by [@PSelleunis](https://github.com/PSelleunis) in
> [PR #44](https://github.com/ThawingLYR/monitoring-portal/pull/44).

Stations are declared in `aws.json` in the
[configuration repository](https://github.com/ThawingLYR/monitoring-portal-configuration)
with `"dataProvider": "netatmo"` and a `sourceID` of `<MAC address>_<module>`,
for example `70:ee:50:1e:00:34_0`. Stations owned by UNIS carry `"owner": "UNIS"`
and are drawn in a distinct colour on the map.

## How it differs from the other sources

| | Frost / Tilsig | Netatmo |
|---|---|---|
| Query | a time range, per station | a bounding box, current values only |
| History | can be backfilled | accumulated by repeated polling |
| Credentials | static | refresh token rotates on every use |

Two consequences follow, and they shape the whole integration:

- **There is no history to fetch.** `getpublicdata` returns only what each station
  reports right now, so the time series exists only because the scheduled job keeps
  appending to it. A gap in the schedule is a permanent gap in the data.
- **One response covers every station.** The API is queried per *area*, not per
  station, so a single request serves all configured stations. The source caches
  each area response for a short time (`RESPONSE_TTL`) and filters it per MAC
  address, which keeps a full pass to a handful of API calls rather than one or two
  per station.

Two bounding boxes are queried, because Netatmo returns only one station per
cluster of overlapping stations when the requested area is large: a tight box
resolves the dense town centre, and a wider box catches the outlying stations.

## Credentials

Four secrets are required. Put them in `.env` locally (see `.env.example`), in
`.streamlit/secrets.toml` for a local Streamlit run, or in the environment of the
`cron-tasks` container in production.

| Variable | What it is |
|---|---|
| `netatmo_client_id` | Client ID of your Netatmo application |
| `netatmo_client_secret` | Client secret of that application |
| `netatmo_first_refresh_token` | Refresh token used to bootstrap the store |
| `local_store_secret_key` | Fernet key encrypting the rotated token at rest |

### 1. Register an application

1. Sign in at [dev.netatmo.com](https://dev.netatmo.com/) with a Netatmo account.
2. Create an application. Note its **client ID** and **client secret**.

### 2. Obtain the first refresh token

On the application page, use the **token generator** to issue a token with the
`read_station` scope, and copy the **refresh token** it produces into
`netatmo_first_refresh_token`.

This value is only a seed. It is used once, on the very first authentication, and
is then replaced (see below).

### 3. Generate the encryption key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Put the result in `local_store_secret_key`. It must be a url-safe base64-encoded
32-byte key, which is **44 characters** long; any other value fails with
`Fernet key must be 32 url-safe base64-encoded bytes`.

Keep this key stable. Changing it makes the stored refresh token unreadable, which
means re-doing step 2.

## The rotating refresh token

Netatmo refresh tokens are **single-use**. Every authentication consumes the token
and returns a replacement, so the replacement has to be stored somewhere writable -
environment variables are read-only from the application's point of view. That is
what `src/auth/secret_manager.py` is for: it keeps the current token in
`secrets/secrets.enc`, encrypted with `local_store_secret_key`.

```
netatmo_first_refresh_token  ──(first run only)──▶  secrets/secrets.enc
                                                     │  rotated on every auth
                                                     ▼
                                              new refresh token
```

Two operational consequences:

- **`secrets/secrets.enc` must survive container recreation.** It is mounted from
  the `secrets` volume in `compose.yml`. If it is lost, the last rotated token goes
  with it, and `netatmo_first_refresh_token` no longer works because it was
  consumed long ago. Recovery means repeating step 2.
- **Do not run two collectors against the same credentials.** Each rotation
  invalidates the other's token. The source authenticates once per pass and shares
  the session between stations, so a single scheduled job is all that is needed.

## Scheduling

`NETATMO_MAX_AGE_MINUTES` (default 15) tells the source how much history to keep
from each response. It exists to avoid re-storing readings the previous pass
already stored.

**It must match the period of the scheduled job.** If the job runs every 30 minutes
while the variable says 15, half of the readings are discarded on arrival and the
series develops gaps. If it is much larger than the period, the same readings are
fetched repeatedly - harmless, since writes are de-duplicated by timestamp, but
wasteful.

## Stored data

Columns are the canonical names used across the portal:

| Netatmo | Stored as |
|---|---|
| `temperature` | `air_temperature` |
| `humidity` | `relative_humidity` |
| `pressure` | `air_pressure` |
| `wind_strength` / `wind_angle` | `wind_speed` / `wind_from_direction` |
| `gust_strength` / `gust_angle` | `wind_speed_of_gust` / `wind_gust_from_direction` |
| `rain_60min` / `rain_24h` | `rainfall_amount_wrt_60min` / `rainfall_amount_wrt_24h` |

A Netatmo station is several hardware modules, and each reports on **its own
timestamp**. The stored frame is therefore sparse: a row carries the columns of one
module and is empty elsewhere. Anything reading these files should resolve values
per column - `Sensor.get_latest_values()` does this - rather than taking the last
row, which would be mostly empty.

Unlike Frost, the column names carry no `-dimension_value` suffix, because a
consumer station has one implicit measurement height. Use
`src/utils/variable_columns.py` to read either convention.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `Fernet key must be 32 url-safe base64-encoded bytes` | `local_store_secret_key` is not a generated Fernet key (step 3) |
| `Authentication failed with status code 400` | The stored refresh token was consumed elsewhere, or the seed token was already used. Redo step 2 |
| `No valid data returned ... for Sensor <id>` | The station is offline, outside both bounding boxes, or reported nothing within `NETATMO_MAX_AGE_MINUTES` |
| Station rows stop appearing after a redeploy | The `secrets` volume was not mounted, so the rotated token was lost |
| `may have changed location` warnings | The station's reported position moved more than 10 m from `aws.json`. Update the configuration, or ignore for a station known to drift |
