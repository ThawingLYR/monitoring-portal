import folium
from typing import Optional
from folium import Element
import json

from src.map.base_map import BaseMap
from src.init.init_insar_map import (
    get_insar_map_Seasonal_Combined,
    get_insar_map_Interannual_Combined,
    get_insar_map_Combined_Seasonal_Interannual,
)
from src.init.init_insar_map import (
    get_image_bounds_Seasonal_Combined,
    get_image_bounds_Interannual_Combined,
    get_image_bounds_Combined_Seasonal_Interannual,
)


class InSARMap(BaseMap):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def customize_map(self):
        """
        Add InSAR image layers to the map (self.m), created by BaseMap.
        Use FeatureGroups so each overlay appears as a separate entry in LayerControl.
        """
        self.m

        # Seasonal
        seasonal_img = get_insar_map_Seasonal_Combined()
        seasonal_bounds = get_image_bounds_Seasonal_Combined()
        fg_seasonal = folium.FeatureGroup(name="Seasonal", overlay=True, show=True)
        folium.raster_layers.ImageOverlay(
            name="Seasonal",
            image=seasonal_img,
            bounds=seasonal_bounds,
            opacity=0.8,
        ).add_to(fg_seasonal)
        fg_seasonal.add_to(self.m)

        # Interannual
        interannual_img = get_insar_map_Interannual_Combined()
        interannual_bounds = get_image_bounds_Interannual_Combined()
        fg_interannual = folium.FeatureGroup(
            name="Interannual", overlay=True, show=False
        )
        folium.raster_layers.ImageOverlay(
            name="Interannual",
            image=interannual_img,
            bounds=interannual_bounds,
            opacity=0.8,
        ).add_to(fg_interannual)
        fg_interannual.add_to(self.m)

        # Combined
        combined_img = get_insar_map_Combined_Seasonal_Interannual()
        combined_bounds = get_image_bounds_Combined_Seasonal_Interannual()
        combined_name = "Combined: Seasonal and Interannual"
        fg_combined = folium.FeatureGroup(name=combined_name, overlay=True, show=False)
        folium.raster_layers.ImageOverlay(
            name=combined_name,
            image=combined_img,
            bounds=combined_bounds,
            opacity=0.8,
        ).add_to(fg_combined)
        fg_combined.add_to(self.m)

        return

    def get_extra_js(self) -> Optional[Element]:
        """
        Inject JavaScript that makes the specified overlay names behave mutually exclusive
        (only one of them can be checked / visible at a time).
        """
        overlay_names = [
            "Seasonal",
            "Interannual",
            "Combined: Seasonal and Interannual",
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
