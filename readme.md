# Waze Pothole Report Sync

Pulls active pothole reports (reported via Waymo vehicles) from the Waze Partner Hub API and syncs them to a Socrata dataset.

## Environment variables

Also shown in `env_template`

| Variable | Description |
|---|---|
| `WAZE_PARTNER_ID` | Waze Partner Hub partner ID |
| `WAZE_TOKEN` | Waze feed access token |
| `SOCRATA_ENDPOINT` | Socrata domain (e.g. `data.example.gov`) |
| `SOCRATA_APP_TOKEN` | Socrata app token |
| `SOCRATA_API_KEY_ID` | Socrata API key ID |
| `SOCRATA_API_KEY_SECRET` | Socrata API key secret |
| `POTHOLE_LOG_DATASET` | Socrata dataset (resource) ID for the pothole log |

## Usage

The easiest way to run this script is to use Docker to build the image and run it with the required environment variables.

Intended to be run on a schedule (we use Airflow) to keep the Socrata pothole log current with the live Waze feed.

### Docker

The repo's Dockerfile copies the whole repo and defaults to running `waze_report_logging.py`:

```bash
docker build -t atddocker/dts-pothole-reporting:local .
docker run --env-file .env atddocker/dts-pothole-reporting:local
```

Or, instead you can pass a specific script to run:

```bash
docker run --env-file .env atddocker/dts-pothole-reporting:local waze/waze_report_logging.py
```

Get an interactive shell instead of running any ETL script, by overriding `--entrypoint`:

```bash
docker run -it --rm --entrypoint /bin/bash --env-file .env atddocker/dts-pothole-reporting:local
```
