from folium.features import GeoJsonPopup, GeoJsonTooltip
import folium

from src.map.base_map import BaseMap

from src.init.init_ground_ice_map import get_gi_poly_gdf, get_gi_mark_gdf


class GroundIceMap(BaseMap):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _define_ground_ice_polygon_style(self, gdf):
        """
        Build and return a style_function and highlight_function for GeoJson polygons.
        """
        color_scale = ["#808080", "#D0CCF5", "#989BE7", "#3669AD", "#293467"]  # devon

        # style_function used by folium.GeoJson
        base = {"fillOpacity": 0.8, "color": "black", "weight": 0.5, "opacity": 1.0}

        # style functions used by folium.GeoJson
        def _style_function(feature):
            style = dict(base)
            style["fillColor"] = color_scale[feature["properties"]["Ground_Ice_Num"]]

            return style

        # highlight function used by folium.GeoJson
        def _highlight_function(feature):
            return {"weight": 3, "color": "#666666", "fillOpacity": 0.85}

        return _style_function, _highlight_function

    def customize_map(self):
        """
        Add ground ice GeoJson layer to the map (self.m), created by BaseMap.
        """
        self.m

        # Load geodataframe and convert to geojson
        gdf_poly = get_gi_poly_gdf()
        geojson_poly = gdf_poly.to_json()

        # Get style and highlight functions
        style_function, highlight_function = self._define_ground_ice_polygon_style(
            gdf_poly
        )

        # Define popup
        popup_poly = GeoJsonPopup(
            fields=["Ground_Ice", "Landform_G", "Ice_type"],
            aliases=[
                "Excess ground ice content (%):",
                "Landform type:",
                "Extra note on ice type:",
            ],
            localize=True,
            labels=True,
            style=(
                "background-color: white; color: #333333; font-family: arial; font-size: 1.2em"
            ),
        )

        # Add GeoJson layer to the map
        folium.GeoJson(
            geojson_poly,
            name="Excess ground ice content: extrapolated",
            style_function=style_function,
            highlight_function=highlight_function,
            popup=popup_poly,
        ).add_to(self.m)

        # also add markers...
        gdf_mark = get_gi_mark_gdf()
        geojson_mark = gdf_mark.to_json()

        custom_marker = folium.CircleMarker(
            radius=6,
            color="black",
            weight=1,
            fill=True,
            fill_color="white",
            fill_opacity=1.0,
        )

        # Define popup
        popup_mark = GeoJsonPopup(
            fields=[
                "ID",
                "Excess_ice",
                "Active_Lay",
                "Depth",
                "Landform_G",
                "Elevation",
            ],
            aliases=[
                "ID:",
                "Excess ground ice content (%):",
                "Active layer depth (m):",
                "Drilling depth (m):",
                "Landform type:",
                "Elevation (m):",
            ],
            localize=True,
            labels=True,
            style=(
                "background-color: white; color: #333333; font-family: arial; font-size: 1.2em"
            ),
        )

        tooltip_mark = GeoJsonTooltip(
            fields=["Excess_ice"],
            aliases=["Excess ground ice content (%):"],
            localize=True,
            labels=True,
            sticky=True,
            style=(
                "background-color: white; color: #333333; font-family: arial; font-size: 1.2em"
            ),
        )

        folium.GeoJson(
            geojson_mark,
            name="Excess ground ice content: observations",
            marker=custom_marker,
            popup=popup_mark,
            tooltip=tooltip_mark,
        ).add_to(self.m)

        return
