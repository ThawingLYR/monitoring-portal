import folium
from typing import Optional


class BaseMap:
    m: Optional[folium.Map] = None

    def __init__(self, location=[78.213578, 15.599462], zoom_start=11):
        # Create map centered near Longyearbyen
        self.m = folium.Map(
            location=location, zoom_start=zoom_start, tiles=None, control_scale=True
        )

        # Basemap layers for different zoom levels
        basemap = folium.FeatureGroup(name="Basemap", overlay=False, show=True)

        folium.raster_layers.WmsTileLayer(
            url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/NP_Basiskart_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
            layers="NP_Basiskart_Svalbard_WMTS_3857",
            fmt="image/png",
            transparent=False,
            version="1.0.0",
            attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a> © 2015 <a href=https://www.npolar.no/en/>Norwegian Polar Insitute</a>",
            name="Basemap low zoom",
            min_zoom=0,
            max_zoom=12,
            overlay=False,
            control=True,
            show=True,
        ).add_to(basemap)

        folium.raster_layers.WmsTileLayer(
            url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/FKB_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
            layers="FKB_Svalbard_WMTS_3857",
            fmt="image/png",
            transparent=False,
            version="1.0.0",
            attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a> © 2015 <a href=https://www.npolar.no/en/>Norwegian Polar Insitute</a>",
            name="Basemap high zoom",
            min_zoom=13,
            max_zoom=17,
            overlay=False,
            control=True,
            show=True,
        ).add_to(basemap)

        basemap.add_to(self.m)

        folium.raster_layers.WmsTileLayer(
            url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/NP_Ortofoto_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
            layers="NP_Ortofoto_Svalbard_WMTS_3857",
            fmt="image/png",
            transparent=False,
            version="1.0.0",
            attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a>",
            name="Orthophoto",
            min_zoom=0,
            max_zoom=17,
            overlay=True,
            control=True,
            show=False,
        ).add_to(self.m)

        folium.raster_layers.WmsTileLayer(
            url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/NP_Satellitt_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
            layers="Basisdata_NP_Satellitt_Svalbard_WMTS_3857",
            fmt="image/png",
            transparent=False,
            version="1.0.0",
            attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a>",
            name="Satellite",
            min_zoom=0,
            max_zoom=17,
            overlay=True,
            control=True,
            show=False,
        ).add_to(self.m)

    def customize_map(self):
        return

    def get_map(self):
        self.customize_map()
        m = self.m
        folium.LayerControl().add_to(m)

        return m
