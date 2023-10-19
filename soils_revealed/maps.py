import warnings
from typing import List

import ee
import folium
from folium.plugins import Draw
import ipyleaflet as ipyl
from shapely.geometry import Polygon


class LeafletMap(ipyl.Map):
    """
    A custom Map class.

    Inherits from ipyl.Map class.
    """

    slugs = ['Landsat-8-Surface-Reflectance', 'Sentinel-2-Top-of-Atmosphere-Reflectance']

    def __init__(self, geometry: dict = None, center: List[float] = [28.4, -16.4], zoom: int = 10, **kwargs):
        """
        Constructor for MapGEE class.

        Parameters:
        center: list, default [28.3904, -16.4409]
            The current center of the map.
        zoom: int, default 10
            The current zoom value of the map.
        geometry: dict, default None
            The current zoom value of the map.
        **kwargs: Additional arguments that are passed to the parent constructor.
        """
        self.geometry = geometry
        if self.geometry:
            self.center = self.centroid
        else:
            self.center = center
        self.zoom = zoom
        
        super().__init__(
            basemap=ipyl.basemap_to_tiles(ipyl.basemaps.Esri.WorldImagery),
            center=tuple(self.center), zoom=self.zoom, **kwargs)

        self.add_draw_control()

    def add_draw_control(self):
        control = ipyl.LayersControl(position='topright')
        self.add_control(control)

        print('Draw a rectangle on map to select and area.')

        draw_control = ipyl.DrawControl()

        draw_control.rectangle = {
            "shapeOptions": {
                "color": "#2BA4A0",
                "fillOpacity": 0,
                "opacity": 1
            }
        }

        if self.geometry:
                self.geometry['features'][0]['properties'] = {'style': {'color': "#2BA4A0", 'opacity': 1, 'fillOpacity': 0}}
                geo_json = ipyl.GeoJSON(
                    data=self.geometry
                )
                self.add_layer(geo_json)

        else:
            feature_collection = {
                'type': 'FeatureCollection',
                'features': []
            }

            def handle_draw(self, action, geo_json):
                """Do something with the GeoJSON when it's drawn on the map"""    
                #feature_collection['features'].append(geo_json)
                if 'pane' in list(geo_json['properties']['style'].keys()):
                    feature_collection['features'] = []
                else:
                    feature_collection['features'] = [geo_json]

            draw_control.on_draw(handle_draw)

            self.add_control(draw_control)

            self.geometry = feature_collection

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

        layer = ipyl.TileLayer(url=tiles_url, name=name)
        self.add_layer(layer)

    @property
    def coordinates(self):
        if not self.geometry['features']:
            warnings.warn("Rectangle hasn't been drawn yet. Polygon is not available.")
            return None

        return self.geometry['features'][0]['geometry']['coordinates'][0]

    @property
    def polygon(self):
        if not self.geometry['features']:
            warnings.warn("Rectangle hasn't been drawn yet. Polygon is not available.")
            return None

        return Polygon(self.coordinates)

    @property
    def bbox(self):
        if not self.polygon:
            warnings.warn("Rectangle hasn't been drawn yet. Bounding box is not available.")
            return None
        
        return list(self.polygon.bounds)
    
    @property
    def centroid(self):
        if not self.geometry['features']:
            warnings.warn("Rectangle hasn't been drawn yet. Centroid is not available.")
            return None
        else:
            return [arr[0] for arr in self.polygon.centroid.xy][::-1]
        


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


