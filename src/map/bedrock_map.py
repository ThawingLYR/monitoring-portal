from folium.features import GeoJsonPopup, GeoJsonTooltip
import folium

from src.map.base_map import BaseMap

from src.init.init_bedrock_map import get_br_poly_gdf, get_br_mark_gdf


class BedrockMap(BaseMap):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _define_bedrock_polygon_style(self, gdf):
        """
        Build and return a style_function and highlight_function for GeoJson polygons.
        """
        color_scale = [
            "#829d4c",
            "#a4c16d",
            "#cde6a4",
            "#eaf4b5",
            "#f6ecae",
            "#ecd097",
            "#d3ac6b",
            "#b98c4b",
        ]  # change to bamako

        # style_function used by folium.GeoJson
        base = {"fillOpacity": 0.8, "color": "black", "weight": 0.5, "opacity": 1.0}

        # style functions used by folium.GeoJson
        def _style_function(feature):
            style = dict(base)
            style["fillColor"] = color_scale[feature["properties"]["gridcode"] - 1]

            return style

        # highlight function used by folium.GeoJson
        def _highlight_function(feature):
            return {"weight": 3, "color": "#666666", "fillOpacity": 0.85}

        return _style_function, _highlight_function

    def customize_map(self):
        """
        Add bedrock GeoJson layer to the map (self.m), created by BaseMap.
        """
        self.m

        # Load geodataframe and convert to geojson
        gdf_poly = get_br_poly_gdf()
        geojson_poly = gdf_poly.to_json()

        # Get style and highlight functions
        style_function, highlight_function = self._define_bedrock_polygon_style(
            gdf_poly
        )

        # Define popup
        popup_poly = GeoJsonPopup(
            fields=["depth_range"],
            aliases=["Interpolated depth to bedrock (m):"],
            localize=True,
            labels=True,
            style=(
                "background-color: white; color: #333333; font-family: arial; font-size: 1.2em"
            ),
        )

        # Add GeoJson layer to the map
        folium.GeoJson(
            geojson_poly,
            name="Depth to bedrock: interpolated",
            style_function=style_function,
            highlight_function=highlight_function,
            popup=popup_poly,
        ).add_to(self.m)

        # also add markers...
        gdf_mark = get_br_mark_gdf()
        geojson_mark = gdf_mark.to_json()

        custom_marker = folium.CircleMarker(
            radius=2,
            color="black",
            weight=1,
            fill=True,
            fill_color="black",
            fill_opacity=1.0,
        )

        # Define popup
        popup_mark = GeoJsonPopup(
            fields=[
                "ID",
                "Reference",
                "Inclinatio",
                "Slope",
                "Z",
                "RL_bedrock",
                "Depth_rock",
            ],
            aliases=[
                "ID:",
                "Reference:",
                "Inclination (°):",
                "Slope (°):",
                "Elevation (m):",
                "Reduced Level (RL) of bedrock:",
                "Depth to bedrock (m):",
            ],
            localize=True,
            labels=True,
            style=(
                "background-color: white; color: #333333; font-family: arial; font-size: 1.2em"
            ),
        )

        tooltip_mark = GeoJsonTooltip(
            fields=["Depth_rock"],
            aliases=["Depth to bedrock (m):"],
            localize=True,
            labels=True,
            sticky=True,
            style=(
                "background-color: white; color: #333333; font-family: arial; font-size: 1.2em"
            ),
        )

        folium.GeoJson(
            geojson_mark,
            name="Depth to bedrock: observations",
            marker=custom_marker,
            popup=popup_mark,
            tooltip=tooltip_mark,
        ).add_to(self.m)

        return
