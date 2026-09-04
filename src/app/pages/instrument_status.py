# Imports
import streamlit as st


# from sources_boreholes_Tilsig import

# Set page configuration
st.set_page_config(page_title="ThawingLYR", layout="wide")
st.title("Instrument status")

st.markdown(
    """
    **Under development** This page will show a map with all relevant instrumentation and what that status is of the instruments, dependent on the last transmission time and other available information (e.g., battery status). The markers at each instrument will be colored (green, orange, red) based on its status and if it needs attention. By clicking on the marker, more information will appear such as set transmission interval, last transmission time, battery status etc.

    This page is specifically useful for instrumentation network maintenance.
    """
)

# # Load instrument status data
# status = instrument_status_Tilsig(sources_tilsig)

# # Create map centered near Longyearbyen
# m = get_folium_basemap()
# folium.LayerControl().add_to(m)

# # Create markers with popup texts and icons
# for i in range(len(marker_tilsig_html)):
#     icon_bh2 = folium.Icon(color="red", icon="temperature-half", prefix="fa")
#     html = folium.Html(marker_tilsig_html[i], script=True)
#     popup = folium.Popup(html, max_width=500)
#     folium.Marker(
#         location=marker_tilsig_coordinates[i],
#         popup=popup,
#         tooltip=marker_tilsig_tooltip[i],
#         icon=icon_bh2,
#     ).add_to(m)

# # call to render Folium map in Streamlit
# st_data = st_folium(
#     m,
#     use_container_width=True,
#     height=450,
#     returned_objects=["last_object_clicked_tooltip"],
# )  # width=1100
