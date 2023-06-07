from typing import List

import ee
import folium
from folium.plugins import Draw


class MapGEE(folium.Map):
    """
    A custom Map class that can display Google Earth Engine tiles.

    Inherits from folium.Map class.
    """

    def __init__(self, center: List[float] = [25.0, 55.0], zoom: int = 3, **kwargs):
        """
        Constructor for MapGEE class.

        Parameters:
        center: list, default [25.0, 55.0]
            The current center of the map.
        zoom: int, default 3
            The current zoom value of the map.
        **kwargs: Additional arguments that are passed to the parent constructor.
        """
        self.center = center
        self.zoom = zoom
        self.geometry = None
        super().__init__(location=self.center, zoom_start=self.zoom, control_scale=True,
                         attr='Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>', **kwargs)

        self.add_draw_control()

    def add_draw_control(self):
        draw = Draw(
            export=False,
            position="topleft",
            draw_options={
                "polyline": False,
                "poly": False,
                "circle": False,
                "polygon": False,
                "marker": False,
                "circlemarker": False,
                "rectangle": True
            }
        )

        draw.add_to(self)

    def add_gee_layer(self, image: ee.Image, sld_interval: str, name: str):
        """
        Add GEE layer to map.

        Parameters:
        image (ee.Image): The Earth Engine image to display.
        sld_interval (str): SLD style of discrete intervals to apply to the image.
        name (str): lLayer name.
        """
        ee_tiles = '{tile_fetcher.url_format}'

        image = image.sldStyle(sld_interval)
        mapid = image.getMapId()
        tiles_url = ee_tiles.format(**mapid)

        tile_layer = folium.TileLayer(
            tiles=tiles_url,
            name=name,
            attr=name,
            overlay=True,
            control=True,
            opacity=1
        )

        tile_layer.add_to(self)

    def add_layer_control(self):
        control = folium.LayerControl(position='topright')

        control.add_to(self)