# Imports
import streamlit as st
from streamlit_folium import st_folium
import folium
import pandas as pd
import branca.colormap as cm
import math

from loguru import logger

from src.app.reusable.folium_basemap import get_folium_basemap

from sources_unis_netatmo_weather_stations import (
    lookup_by_station_address_NETATMO,
)

from src.app.loader.load_NETATMO_weather_stations import (
    load_data_NETATMO,
    NETATMO_data_to_dataframe,
)


def select_metric(metric: str):
    st.session_state.selected_metric = metric


def metric_button(label: str, metric: str, key: str):
    return st.button(
        label,
        key=key,
        on_click=select_metric,
        args=(metric,),
        type=("primary" if st.session_state.selected_metric == metric else "secondary"),
        use_container_width=True,
    )


def reload_data(seconds: int = 60):
    if st.session_state.last_refresh_time < pd.Timestamp.now() - pd.Timedelta(
        seconds=seconds
    ):
        logger.info("Manual refresh triggered.")
        load_data_NETATMO.clear()
        st.session_state.last_refresh_time = pd.Timestamp.now()
    else:
        st.toast(
            "Data was refreshed recently. Please wait before refreshing again.",
            icon="⏳",
        )


def check_availability(df: pd.DataFrame):
    if df.empty:
        return df

    df["data_availability"] = "No data"
    for row in df.iterrows():
        av_metric = set()
        for metric_info in metrics.values():
            if metric_info["df_time_col"] in df.columns:
                if not pd.isna(row[1][metric_info["df_time_col"]]):
                    av_metric.add(metric_info["legend"].split(" ")[0])
        if len(av_metric) > 0:
            df.at[row[0], "data_availability"] = ", ".join(av_metric)

    return df


metrics = {
    "temp": {
        "infotext": "Temperature in °C measured in the last 20 minutes.",
        "df_col": ["temperature"],
        "df_time_col": "temp_timeutc",
        "icon": "temperature-low",
        "text": ["", "°C"],
        "legend": "Temperature (°C)",
    },
    "wind_g": {
        "infotext": "Wind gust in m/s measured in the last 20 minutes.",
        "df_col": ["gust_strength", "gust_angle"],
        "df_time_col": "wind_timeutc",
        "icon": "arrow-down",
        "text": ["", "m/s", "°"],
        "legend": "Wind Gust (m/s)",
    },
    "wind_s": {
        "infotext": "Wind strength in m/s measured in the last 20 minutes.",
        "df_col": ["wind_strength", "wind_angle"],
        "df_time_col": "wind_timeutc",
        "icon": "arrow-down",
        "text": ["", "m/s", "°"],
        "legend": "Wind Strength (m/s)",
    },
    "rain_60": {
        "infotext": "Rain in mm in the last 60 minutes.",
        "df_col": ["rain_60min"],
        "df_time_col": "rain_timeutc",
        "icon": "droplet",
        "text": ["", "mm"],
        "legend": "Rain (mm)",
    },
    "rain_24": {
        "infotext": "Rain in mm in the last 24 hours.",
        "df_col": ["rain_24h"],
        "df_time_col": "rain_timeutc",
        "icon": "droplet",
        "text": ["", "mm"],
        "legend": "Rain (mm)",
    },
    "hum": {
        "infotext": "Humidity in % measured in the last 20 minutes.",
        "df_col": ["humidity"],
        "df_time_col": "temp_timeutc",
        "icon": "tint",
        "text": ["", "%"],
        "legend": "Humidity (%)",
    },
    "p": {
        "infotext": "Pressure in hPa measured in the last 20 minutes.",
        "df_col": ["pressure"],
        "df_time_col": "pres_timeutc",
        "icon": "tachometer",
        "text": ["", "hPa"],
        "legend": "Pressure (hPa)",
    },
}

if "selected_metric" not in st.session_state:
    st.session_state.selected_metric = "temp"
if "last_refresh_time" not in st.session_state:
    st.session_state.last_refresh_time = pd.Timestamp.now()

unsorted_data = load_data_NETATMO()
data = NETATMO_data_to_dataframe(unsorted_data)
data = check_availability(data)

# Set page configuration
st.set_page_config(page_title="NETATMO weather stations", layout="wide")
st.title("NETATMO weather stations")

colT, colWS, colWG, colR60, colR24, colH, colp = st.columns(7)

with colT:
    metric_button(
        "Temperature",
        "temp",
        "btn_T",
    )
with colWG:
    metric_button(
        "Wind gust",
        "wind_g",
        "btn_wg",
    )
with colWS:
    metric_button(
        "Wind strength",
        "wind_s",
        "btn_ws",
    )
with colR60:
    metric_button(
        "Rain 60min",
        "rain_60",
        "btn_r60",
    )
with colR24:
    metric_button(
        "Rain 24h",
        "rain_24",
        "btn_r24",
    )
with colH:
    metric_button(
        "Humidity",
        "hum",
        "btn_h",
    )
with colp:
    metric_button(
        "Pressure",
        "p",
        "btn_p",
    )

# setting the right dict
selected_metric_data = metrics[st.session_state.selected_metric]
# text over map
st.markdown(
    f"**{selected_metric_data['infotext']}**",
)

map_col, legend_col = st.columns([9, 1])

m = get_folium_basemap()

if not selected_metric_data["df_col"][0] in data.columns:
    st.warning("No data available for the selected metric.")
    load_data_NETATMO.clear()
    st.stop()

# creating color map
if math.floor(data[selected_metric_data["df_col"][0]].min()) == math.ceil(
    data[selected_metric_data["df_col"][0]].max()
):
    metric_cm = cm.linear.viridis.scale(
        math.floor(data[selected_metric_data["df_col"][0]].min()),
        math.ceil(data[selected_metric_data["df_col"][0]].max()) + 1,
    )
else:
    metric_cm = cm.linear.viridis.scale(
        math.floor(data[selected_metric_data["df_col"][0]].min()),
        math.ceil(data[selected_metric_data["df_col"][0]].max()),
    )

# add station markers
for row in data.iterrows():
    if pd.isna(row[1][selected_metric_data["df_time_col"]]):
        logger.info(
            "Skipping station lat:{0:.3f}/lon:{1:.3f} without data for selected metric.".format(
                row[1]["latitude"], row[1]["longitude"]
            )
        )
        continue  # skip stations without data for selected metric
    else:
        marker = f"""<body style="font-family:sans-serif; font-size:0.5em">"""
        # checking if data is recent (last 20 minutes)
        time = pd.to_datetime(row[1][selected_metric_data["df_time_col"]], unit="s")
        if time < pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=20):
            logger.info(
                "Skipping station lat:{0:.3f}/lon:{1:.3f} with outdated ({2}) data for selected metric.".format(
                    row[1]["latitude"],
                    row[1]["longitude"],
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                )
            )
            continue  # skip stations with outdated data for selected metric
        marker += f"""<b>ID</b>: {row[1]["station_id"]}<br>"""
        text = (
            selected_metric_data["text"][0]
            + str(row[1][selected_metric_data["df_col"][0]])
            + selected_metric_data["text"][1]
        )
        i_color = metric_cm(row[1][selected_metric_data["df_col"][0]])
        if len(selected_metric_data["df_col"]) == 2:
            i_angle = math.floor(row[1][selected_metric_data["df_col"][1]])
            text += " | " + str(i_angle) + selected_metric_data["text"][2]
        else:
            i_angle = 0
        marker += f"""<b>{' '.join(selected_metric_data['legend'].split(' ')[:-1])}</b>: {text}<br>"""
        if row[1]["station_id"] in lookup_by_station_address_NETATMO:
            color = "darkred"
            mac = row[1]["station_id"]
            lat = lookup_by_station_address_NETATMO[mac]["lat"]
            if pd.isna(lat):
                lat = row[1]["latitude"]
            lon = lookup_by_station_address_NETATMO[mac]["lon"]
            if pd.isna(lon):
                lon = row[1]["longitude"]
            marker += f"""<b>UNIS Station</b>: {lookup_by_station_address_NETATMO[mac]["station"]}<br>"""
        else:
            color = "white"
            lat = row[1]["latitude"]
            lon = row[1]["longitude"]
        icon = folium.Icon(
            color=color,
            icon=selected_metric_data["icon"],
            icon_color=i_color,
            angle=i_angle,
            prefix="fa",
        )
        marker += f"""<b>Data availability</b>: {row[1]["data_availability"]}<br>"""
        marker += f"""</body>"""
        html = folium.Html(marker, script=True)
        popup = folium.Popup(html, max_width=250)
        folium.Marker(
            location=[lat, lon],
            tooltip=text,
            popup=popup,
            icon=icon,
        ).add_to(m)


# Add a legend
legend_html = """
<div style="
    position: fixed;
    bottom: 50px;
    left: 5px;
    width: 180px;
    background-color: white;
    border-radius: 4px;
    border: 2px solid grey;
    z-index: 9999;
    font-size: 14px;
    padding: 10px;
    color: black;
">
<p style="margin: 0 0 8px 0;"><b>Station Type</b></p>

<p style="margin: 0 0 6px 0;">
    <span style="
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: darkred;
        border: 1px solid black;
        border-radius: 50%;
        margin-right: 8px;
        vertical-align: middle;
    "></span>
    UNIS Station
</p>

<p style="margin: 0;">
    <span style="
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: white;
        border: 1px solid black;
        border-radius: 50%;
        margin-right: 8px;
        vertical-align: middle;
    "></span>
    Private/Other <br>
    <span style="margin-left: 23px;">Organization Station
</p>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

with map_col:
    # call to render Folium map in Streamlit
    st_data = st_folium(
        m,
        use_container_width=True,
        height=450,
        returned_objects=["last_object_clicked_popup"],
    )  # width=1100


with legend_col:
    # Title or padding to align with the map layout
    st.markdown(f"{selected_metric_data['legend']}")

    # 2. Pure HTML/CSS Vertical Legend
    step_diff = (metric_cm.vmax - metric_cm.vmin) / 4
    st.html(f"""
        <div style="display: flex; flex-direction: row; height: 340px; align-items: stretch;">
            <div style="
                background: linear-gradient(to top, #440154, #3b528b, #21918c, #5ec962, #fde725);
                width: 16px;
                border-radius: 4px;
            "></div>
            
            <div style="
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                padding-left: 10px;
                height: 100%;
                font-size: 13px;
                font-family: sans-serif;
                white-space: nowrap;
                color: gray;
            ">
                <span>{metric_cm.vmax}</span>
                <span>{metric_cm.vmin+step_diff*3}</span>
                <span>{metric_cm.vmin+step_diff*2}</span>
                <span>{metric_cm.vmin+step_diff}</span>
                <span>{metric_cm.vmin}</span>
            </div>
        </div>
    """)

col1, col2, col3, col4 = st.columns(4)

with col4:
    st.button("Refresh data", on_click=reload_data, use_container_width=True)
