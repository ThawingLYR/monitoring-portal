# Imports
import pandas as pd
import requests
import numpy as np
import streamlit as st

from loguru import logger

from src.auth.NETATMO import get_bearer_token as get_netatmo_bearer_token

###########################################
### Data loading from NETATMO functions ###
###########################################


@st.cache_data(ttl=1200)
def load_data_NETATMO():

    logger.info(f"Loading data from NETATMO API")

    ######################
    ### Authentication ###
    ######################

    bearer_token = get_netatmo_bearer_token()

    ######################
    ### Data retrieval ###
    ######################

    lyr_coords = [78.226902, 15.689416, 78.216516, 15.590670]
    big_area_coords = [78.25, 16.3, 78.15, 15.3]
    coords = [lyr_coords, big_area_coords]

    try:
        i = 0
        data = {}
        for lat_ne, lon_ne, lat_sw, lon_sw in coords:
            # Create the request URL for fetching public data
            # Define the area you want to get data from
            # If the area is too big, not all stations are found
            url = "https://api.netatmo.com/api/getpublicdata"
            params = {
                "lat_ne": lat_ne,
                "lon_ne": lon_ne,
                "lat_sw": lat_sw,
                "lon_sw": lon_sw,
                "required_data": "temperature",
                "filter": False,
            }
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {bearer_token}",
            }

            # Make a GET request to retrieve the data
            response = requests.get(url, params=params, headers=headers)
            data_2_check = response.json()
            if status := data_2_check.get("status", None) != "ok":
                logger.error(
                    f"Error fetching data from NETATMO API for coordinates {coords[i]}: {data_2_check.get('error', {}).get('message', 'No error message provided')}"
                )
            else:
                data[i] = data_2_check
            i += 1

    except Exception as e:
        logger.error(f"Error during data retrieval: {e}")
        return None

    return data


def NETATMO_data_to_dataframe(data):
    Structured_data_ls = []
    for data_part in data.values():
        structured_data = []
        time_server = data_part["time_server"]
        for entry in data_part["body"]:
            _id = entry["_id"]
            longitude, latitude = entry["place"]["location"]
            if "timezone" in entry["place"]:
                timezone = entry["place"]["timezone"]
            else:
                timezone = np.nan
                logger.warning(f"No timezone info for station {_id}.")
            if "altitude" in entry["place"]:
                altitude = entry["place"]["altitude"]
            else:
                altitude = np.nan
                logger.warning(f"No altitude info for station {_id}.")

            temperature, humidity, pressure = None, None, None
            if "measures" in entry:
                measures = entry["measures"]
                for sensor, sensor_data in measures.items():
                    if "type" in sensor_data and "res" in sensor_data:
                        res_time = int(
                            list(sensor_data["res"].keys())[0]
                        )  # Extract timestamp
                        res_values = sensor_data["res"][
                            str(res_time)
                        ]  # Sensor readings

                        if "temperature" in sensor_data["type"]:
                            temperature = res_values[0]  # First value is temperature
                            temp_time = res_time  # Timestamp for temperature
                        if "humidity" in sensor_data["type"]:
                            humidity = res_values[1]  # Second value is humidity
                        if "pressure" in sensor_data["type"]:
                            pressure = res_values[0]  # Pressure has only one value
                            pres_time = res_time  # Timestamp for pressure

            wind_strength, wind_angle, gust_strength, gust_angle, wind_timeutc = (
                None,
                None,
                None,
                None,
                None,
            )
            if "modules" in entry:
                modules = entry["modules"]
                for module in modules:
                    if module.startswith("06:00:00") and module in measures:
                        wind_data = measures[module]
                        wind_strength = wind_data.get("wind_strength", None)
                        wind_angle = wind_data.get("wind_angle", None)
                        gust_strength = wind_data.get("gust_strength", None)
                        gust_angle = wind_data.get("gust_angle", None)
                        wind_timeutc = wind_data.get("wind_timeutc", None)

            rain_60min, rain_24h, rain_live, rain_timeutc = None, None, None, None
            if "modules" in entry:
                modules = entry["modules"]
                for module in modules:
                    if module.startswith("05:00:00") and module in measures:
                        rain_data = measures[module]
                        rain_60min = rain_data.get("rain_60min", None)
                        rain_24h = rain_data.get("rain_24h", None)
                        rain_live = rain_data.get("rain_live", None)
                        rain_timeutc = rain_data.get("rain_timeutc", None)

            structured_data.append(
                {
                    "station_id": _id,
                    "time_server": time_server,
                    "latitude": latitude,
                    "longitude": longitude,
                    "timezone": timezone,
                    "altitude": altitude,
                    "temperature": temperature,
                    "humidity": humidity,
                    "temp_timeutc": temp_time,
                    "pressure": pressure,
                    "pres_timeutc": pres_time,
                    "wind_strength": wind_strength,
                    "wind_angle": wind_angle,
                    "gust_strength": gust_strength,
                    "gust_angle": gust_angle,
                    "wind_timeutc": wind_timeutc,
                    "rain_60min": rain_60min,
                    "rain_24h": rain_24h,
                    "rain_live": rain_live,
                    "rain_timeutc": rain_timeutc,
                }
            )
            df_netatmo = pd.DataFrame(
                structured_data,
                columns=[
                    "station_id",
                    "time_server",
                    "latitude",
                    "longitude",
                    "timezone",
                    "altitude",
                    "temperature",
                    "humidity",
                    "temp_timeutc",
                    "pressure",
                    "pres_timeutc",
                    "wind_strength",
                    "wind_angle",
                    "gust_strength",
                    "gust_angle",
                    "wind_timeutc",
                    "rain_60min",
                    "rain_24h",
                    "rain_live",
                    "rain_timeutc",
                ],
            )
            Structured_data_ls.append(df_netatmo)

    if len(Structured_data_ls) == 0:
        logger.warning("No valid data retrieved from NETATMO API.")
        return pd.DataFrame()  # Return empty DataFrame if no data
    elif len(Structured_data_ls) == 1:
        df = Structured_data_ls[0]
    else:
        df = pd.concat(Structured_data_ls, ignore_index=True)

    df = df.drop_duplicates(subset=["station_id"], keep="last", ignore_index=True)
    df["time"] = pd.to_datetime(df["time_server"], unit="s").dt.tz_localize("UTC")
    df["temp_timeutc"] = pd.to_datetime(df["temp_timeutc"], unit="s").dt.tz_localize(
        "UTC"
    )
    df["wind_timeutc"] = pd.to_datetime(df["wind_timeutc"], unit="s").dt.tz_localize(
        "UTC"
    )
    df["rain_timeutc"] = pd.to_datetime(df["rain_timeutc"], unit="s").dt.tz_localize(
        "UTC"
    )
    df["pres_timeutc"] = pd.to_datetime(df["pres_timeutc"], unit="s").dt.tz_localize(
        "UTC"
    )

    return df
