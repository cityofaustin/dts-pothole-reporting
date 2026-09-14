# Logs current Waze pothole reports from Waymo vehicles in Socrata
from datetime import datetime
import logging
import os
from zoneinfo import ZoneInfo

import requests
from sodapy import Socrata

import utils

PARTNER_ID = os.getenv("WAZE_PARTNER_ID")
WAZE_TOKEN = os.getenv("WAZE_TOKEN")

SOCRATA_ENDPOINT = os.getenv("SOCRATA_ENDPOINT")
SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")
SOCRATA_API_KEY_ID = os.getenv("SOCRATA_API_KEY_ID")
SOCRATA_API_KEY_SECRET = os.getenv("SOCRATA_API_KEY_SECRET")
POTHOLE_LOG_DATASET = os.getenv("POTHOLE_LOG_DATASET")


def retrieve_current_potholes():
    url = f"https://www.waze.com/partnerhub-api/partners/{PARTNER_ID}/waze-feeds/{WAZE_TOKEN}?format=1&types=alerts&astf=HAZARD_ON_ROAD_POT_HOLE&ofa=TRUE"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def retrieve_stored_active_potholes(soda_client):
    active = soda_client.get(
        POTHOLE_LOG_DATASET, select="uuid", where="status == 'active'"
    )
    logger.info(f"Retrieved {len(active)} active pothole reports from Socrata")
    return [a["uuid"] for a in active]


def create_wkt_point(x, y):
    # Creates well-known text (WKT) point for a given x and y coordinate
    if x and y:
        return f"POINT({x} {y})"
    raise ValueError("X and/or Y coordinates not provided")


def mills_to_socrata_timestamp(mills, local_tz="America/Chicago"):
    if mills and type(mills) == int:
        # converts a millisecond timestamp to local timestamp and UTC timestamp in the format expected by Socrata
        central_time = datetime.fromtimestamp(
            mills / 1000.0, tz=ZoneInfo(local_tz)
        ).strftime("%Y-%m-%dT%H:%M:%S")
        utc_time = datetime.fromtimestamp(mills / 1000.0, tz=ZoneInfo("UTC")).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        return central_time, utc_time
    raise ValueError("Missing or incorrect timestamp provided")


def string_to_boolean(string):
    if string == "true":
        return True
    elif string == "false":
        return False
    else:
        raise ValueError("Invalid boolean string")


def upsert_pothole_log(data, soda_client):
    logger.info(f"Upserting {len(data)} pothole records to Socrata")
    response = soda_client.upsert(POTHOLE_LOG_DATASET, data)
    return response


def main():
    client = Socrata(
        SOCRATA_ENDPOINT,
        SOCRATA_APP_TOKEN,
        username=SOCRATA_API_KEY_ID,
        password=SOCRATA_API_KEY_SECRET,
        timeout=15,
    )

    # 1. get current potholes
    data = retrieve_current_potholes()

    # 2. get stored active potholes from Socrata
    active_uuids = retrieve_stored_active_potholes(soda_client=client)
    current_uuids = [record["uuid"] for record in data["alerts"]]

    updates_to_socrata = []
    # 3. check if any potholes have been removed from the waze feed, and set the status of those stored as 'archived'
    for uuid in active_uuids:
        if uuid not in current_uuids:
            updates_to_socrata.append(
                {
                    "uuid": uuid,
                    "status": "archived",
                    "archived_date": datetime.now(ZoneInfo("America/Chicago")).strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    ),
                }
            )

    # 4. clean up the data for currently active pothole reports
    for record in data["alerts"]:
        record["status"] = "active"
        record["location"] = create_wkt_point(
            record["location"]["x"], record["location"]["y"]
        )
        (
            record["published_datetime_local"],
            record["published_datetime_utc"],
        ) = mills_to_socrata_timestamp(record["pubMillis"])
        record["reportByMunicipalityUser"] = string_to_boolean(
            record["reportByMunicipalityUser"]
        )
        updates_to_socrata.append(record)

    # 5. send updates to socrata
    res = upsert_pothole_log(updates_to_socrata, soda_client=client)
    logger.info(res)


logger = utils.get_logger(
    __name__,
    level=logging.INFO,
)

if __name__ == "__main__":
    main()
