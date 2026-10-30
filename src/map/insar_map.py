import folium
from src.map.base_map import BaseMap
from src.init.init_insar_map import get_insar_map
from src.init.init_insar_map import get_image_bounds


class InSARMap(BaseMap):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def customize_map(self):
        """
        Add InSAR image layer to the map (self.m), created by BaseMap.
        """
        self.m

        # Load
        data_url = get_insar_map()
        image_bounds = get_image_bounds()

        folium.raster_layers.ImageOverlay(
            name="Combined: seasonal-interannual",
            image=data_url,
            bounds=image_bounds,
            opacity=0.8,
        ).add_to(self.m)

        return
