from folium.features import GeoJsonPopup
import folium
from typing import Optional
from folium import Element
import json

from src.map.base_map import BaseMap
from src.init.init_ch_map import get_ch_gdf


class RiskCHMap(BaseMap):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _define_ch_polygon_style(self):
        """
        Build and return a style_function and highlight_function for GeoJson polygons.
        """

        color_scale_risk = [
            "#FFFECB",
            "#FBE890",
            "#F3CA5F",
            "#ECAC54",
            "#E79452",
            "#E27B50",
            "#D9604E",
            "#BB4B48",
            "#8F403D",
            "#67342A",
            "#452918",
            "#2C200B",
            "#191900",
        ]  # lajolla
        color_scale_vulnerability = [
            "#FFE599",
            "#C5AE32",
            "#71870B",
            "#3A652A",
            "#00404D",
        ]  # bamako
        color_scale_hazard = ["#E6E6F0", "#D495B8", "#926390", "#2E214D"]  # acton

        base = {"fillOpacity": 0.8, "color": "black", "weight": 0.5, "opacity": 1.0}

        # style functions used by folium.GeoJson
        def _style_function_risk(feature):
            style = dict(base)
            style["fillColor"] = color_scale_risk[feature["properties"]["R_CH"]]

            return style

        def _style_function_vuln(feature):
            style = dict(base)
            style["fillColor"] = color_scale_vulnerability[
                feature["properties"]["V_CH"]
            ]

            return style

        def _style_function_hnorm(feature):
            style = dict(base)
            style["fillColor"] = color_scale_hazard[feature["properties"]["H_norm"] - 1]

            return style

        def _style_function_hgm(feature):
            style = dict(base)
            style["fillColor"] = color_scale_hazard[feature["properties"]["H_Geom"] - 1]

            return style

        def _style_function_hinsar(feature):
            style = dict(base)
            style["fillColor"] = color_scale_hazard[
                feature["properties"]["H_InSAR"] - 1
            ]

            return style

        def _style_function_hcoast(feature):
            style = dict(base)
            style["fillColor"] = color_scale_hazard[
                feature["properties"]["H_Coastal"] - 1
            ]

            return style

        # highlight function used by folium.GeoJson
        def _highlight_function(feature):
            return {"weight": 3, "color": "#666666", "fillOpacity": 1.0}

        return (
            _style_function_risk,
            _style_function_vuln,
            _style_function_hnorm,
            _style_function_hgm,
            _style_function_hinsar,
            _style_function_hcoast,
            _highlight_function,
        )

    def _popup(self):
        """
        Build and return a popup for GeoJson polygons.
        """
        popup = GeoJsonPopup(
            fields=[
                "CH_type_NO",
                "Desc_NO",
                "R_CH",
                "V_CH",
                "H_norm",
                "H_Geom",
                "H_InSAR",
                "H_Coastal",
            ],
            aliases=[
                "Building type code:",
                "Description:",
                "Risk score:",
                "Vulnerability score:",
                "Normalized hazard score:",
                "\u00a0\u00a0\u00a0\u2022\u00a0Geomorphology:",
                "\u00a0\u00a0\u00a0\u2022\u00a0InSAR:",
                "\u00a0\u00a0\u00a0\u2022\u00a0Coastal:",
            ],
            localize=True,
            labels=True,
            style=(
                "background-color: white; color: #333333; font-family: arial; font-size: 1.2em"
            ),
        )
        return popup

    def customize_map(self):
        """
        Add modern buildings GeoJson layer to the map (self.m), created by BaseMap.
        """
        self.m

        # Load geodataframe and convert to geojson
        gdf = get_ch_gdf()
        geojson = gdf.to_json()

        # Get style and highlight functions
        (
            style_function_risk,
            style_function_vuln,
            style_function_hnorm,
            style_function_hgm,
            style_function_hinsar,
            style_function_hcoast,
            highlight_function,
        ) = self._define_ch_polygon_style()

        # Get popup (folium errors when using the same popup on multiple GeoJson layers)
        popup1 = self._popup()
        popup2 = self._popup()
        popup3 = self._popup()
        popup4 = self._popup()
        popup5 = self._popup()
        popup6 = self._popup()

        # Add GeoJson layers to the map
        fg_risk = folium.FeatureGroup(name="Risk score", overlay=True, show=True)
        folium.GeoJson(
            geojson,
            name="Risk score",
            style_function=style_function_risk,
            highlight_function=highlight_function,
            popup=popup1,
        ).add_to(fg_risk)
        fg_risk.add_to(self.m)

        fg_vuln = folium.FeatureGroup(
            name="Vulnerability score", overlay=True, show=False
        )
        folium.GeoJson(
            geojson,
            name="Vulnerability score",
            style_function=style_function_vuln,
            highlight_function=highlight_function,
            popup=popup2,
        ).add_to(fg_vuln)
        fg_vuln.add_to(self.m)

        fg_hnorm = folium.FeatureGroup(
            name="Hazard score: Normalized", overlay=True, show=False
        )
        folium.GeoJson(
            geojson,
            name="Hazard score: Normalized",
            style_function=style_function_hnorm,
            highlight_function=highlight_function,
            popup=popup3,
        ).add_to(fg_hnorm)
        fg_hnorm.add_to(self.m)

        fg_hgm = folium.FeatureGroup(
            name="Hazard score: Geomorphology", overlay=True, show=False
        )
        folium.GeoJson(
            geojson,
            name="Hazard score: Geomorphology",
            style_function=style_function_hgm,
            highlight_function=highlight_function,
            popup=popup4,
        ).add_to(fg_hgm)
        fg_hgm.add_to(self.m)

        fg_hinsar = folium.FeatureGroup(
            name="Hazard score: InSAR", overlay=True, show=False
        )
        folium.GeoJson(
            geojson,
            name="Hazard score: InSAR",
            style_function=style_function_hinsar,
            highlight_function=highlight_function,
            popup=popup5,
        ).add_to(fg_hinsar)
        fg_hinsar.add_to(self.m)

        fg_hcoastal = folium.FeatureGroup(
            name="Hazard score: Coastal", overlay=True, show=False
        )
        folium.GeoJson(
            geojson,
            name="Hazard score: Coastal",
            style_function=style_function_hcoast,
            highlight_function=highlight_function,
            popup=popup6,
        ).add_to(fg_hcoastal)
        fg_hcoastal.add_to(self.m)

        return

    def get_extra_js(self) -> Optional[Element]:

        # Inject JavaScript that makes the two overlay checkboxes behave like radio buttons
        # (only one of the specified overlayNames can be checked at any time)
        overlay_names = [
            "Risk score",
            "Vulnerability score",
            "Hazard score: Normalized",
            "Hazard score: Geomorphology",
            "Hazard score: InSAR",
            "Hazard score: Coastal",
        ]
        overlay_json = json.dumps(overlay_names)

        js_template = """
        <script>
        (function() {{
            // Makes the specified overlay layers behave as mutually exclusive (radio-like)
            // overlayNames should be an array of exact layer names (case-sensitive).
            function makeExclusive(names) {{
                var attempts = 0;
                var syntheticFlag = 'data-synthetic-click';

                function setup() {{
                    var inputs = document.getElementsByClassName('leaflet-control-layers-selector');
                    if (!inputs || inputs.length === 0) {{
                        if (attempts++ < 30) {{ setTimeout(setup, 200); }}
                        return;
                    }}

                    for (var i = 0; i < inputs.length; i++) {{
                        (function(i) {{
                            var input = inputs[i];
                            var labelNode = input.nextSibling;
                            if (!labelNode) return;
                            var label = (labelNode.innerText || labelNode.textContent || '').trim();
                            if (names.indexOf(label) === -1) return;

                            // When this overlay is checked, uncheck (click) other overlays in the group
                            input.addEventListener('change', function() {{
                                if (!this.checked) return; // only handle checks
                                for (var j = 0; j < inputs.length; j++) {{
                                    var other = inputs[j];
                                    if (other === this) continue;
                                    var otherLabelNode = other.nextSibling;
                                    if (!otherLabelNode) continue;
                                    var otherLabel = (otherLabelNode.innerText || otherLabelNode.textContent || '').trim();
                                    if (names.indexOf(otherLabel) === -1) continue;
                                    if (other.checked) {{
                                        // mark synthetic to avoid re-entrancy if needed
                                        other.setAttribute(syntheticFlag, '1');
                                        // simulate a real user click so Leaflet toggles properly
                                        var ev = new MouseEvent('click', {{view: window, bubbles: true, cancelable: true}});
                                        other.dispatchEvent(ev);
                                        // remove the synthetic marker shortly after
                                        (function(el) {{
                                            setTimeout(function(){{ el.removeAttribute(syntheticFlag); }}, 50);
                                        }})(other);
                                    }}
                                }}
                            }});

                            // Optional guard: if clicked programmatically and you need to detect that,
                            // check input.getAttribute(syntheticFlag) in other handlers.
                            input.addEventListener('click', function(e) {{
                                // no-op placeholder for potential future logic
                            }});
                        }})(i);
                    }}
                }}
                setup();
            }}

            var overlayNames = {overlay_json};
            if (document.readyState === 'complete') {{
                makeExclusive(overlayNames);
            }} else {{
                window.addEventListener('load', function() {{ makeExclusive(overlayNames); }});
            }}
        }})();
        </script>
        """

        js = js_template.format(overlay_json=overlay_json)

        return Element(js)
