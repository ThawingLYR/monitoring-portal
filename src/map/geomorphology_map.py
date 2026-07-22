from folium.plugins import StripePattern
from folium.features import GeoJsonPopup
import folium

from src.map.base_map import BaseMap

from src.init.init_geomorph_map import get_geomorph_gdf, get_geomorph_mapping


class GeomorphologyMap(BaseMap):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _define_geomorph_polygon_style(self, gdf):
        """
        Build and return a style_function and highlight_function for GeoJson polygons.
        """
        # Find JORDART values that should be striped
        striped_jordarts = sorted(
            gdf.loc[gdf["striped"] == "yes", "JORDART"].unique().tolist()
        )

        # Get style mapping for JORDART
        mapping = get_geomorph_mapping()

        # Pre-build stripe patterns for striped JORDART values
        patterns = {}
        for striped_jordart in striped_jordarts:
            landform_color = mapping.get(str(striped_jordart), {}).get(
                "landform_color", None
            )
            pattern = StripePattern(
                angle=45,
                weight=4,
                color="#ffffff",
                space_color=landform_color,
                space_weight=4,
                opacity=1.0,
                space_opacity=1.0,
            )
            patterns[striped_jordart] = pattern

        # style_function used by folium.GeoJson
        def _style_function(feature):

            default_style = {
                "fillOpacity": 0.7,
                "fillColor": feature["properties"]["landform_color"],
                "color": "black",
                "weight": 0.5,
                "opacity": 1.0,
            }

            if feature["properties"]["JORDART"] in striped_jordarts:
                default_style["fillPattern"] = patterns[
                    feature["properties"]["JORDART"]
                ]

            return default_style

        # highlight function used by folium.GeoJson
        def _highlight_function(feature):
            return {"weight": 3, "color": "#666666", "fillOpacity": 0.85}

        return _style_function, _highlight_function

    def customize_map(self):
        """
        Add geomorphology GeoJson layer to the map (self.m), created by BaseMap.
        """
        self.m

        # Load geodataframe and convert to geojson
        gdf = get_geomorph_gdf()
        geojson = gdf.to_json()

        # Get style and highlight functions
        style_function, highlight_function = self._define_geomorph_polygon_style(gdf)

        # Define popup
        popup = GeoJsonPopup(
            fields=["JORDART", "landform_description_en"],
            aliases=["Jordart:", "Description:"],
            localize=True,
            labels=True,
            style=(
                "background-color: white; color: #333333; font-family: arial; font-size: 1.2em"
            ),
        )

        # Add GeoJson layer to the map
        folium.GeoJson(
            geojson,
            name="Geomorphology",
            style_function=style_function,
            highlight_function=highlight_function,
            popup=popup,
        ).add_to(self.m)

        return
