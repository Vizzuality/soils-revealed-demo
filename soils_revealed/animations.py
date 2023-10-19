import io
import time
import requests
from PIL import Image

import ee
import numpy as np
from shapely.geometry import shape

from data_params import SatelliteImageryData


class Animation:
    """
    Create animations.
    ----------
    """
    def __init__(self, instrument):
        self.instrument = instrument
        if instrument == 'Landsat':
            self.slug = 'Landsat-8-Surface-Reflectance'
        elif instrument == 'Sentinel':
            self.slug = 'Sentinel-2-Top-of-Atmosphere-Reflectance'
        else:
            raise ValueError("Instrument must be either 'Landsat' or 'Sentinel'")
        
    def create_collection(self, start_year, stop_year):
        """
        Create a GEE ImageCollection with 1 composite per year.
        ----------
        start_year : int
            First year
        stop_year : int
            Last year
        """

        years = np.arange(start_year , stop_year+1)

        instrument_data = SatelliteImageryData(instrument=self.instrument)
        
        dic = instrument_data.date_range
        years_range = list(map(list, list(dic.values())))
        slugs = list(dic.keys())
        
        images = []
        for year in years:
            n = 0
            in_range = False
            for sub_years in years_range:
                if year in sub_years:
                    in_range = True
                    break
                n =+ 1 
                
            if not in_range:
                raise ValueError(f'Year out of range.')
                
            slug = slugs[n]
            gee_data =  SatelliteImageryData(dataset=slug)
            
            self.scale = gee_data.scale
      
            # Image Visualization parameters
            vis = gee_data.vizz_params_rgb
            
            step_range = gee_data.step_range
            
            startDate = ee.Date(str(year+step_range[0])+'-12-31')
            stopDate  = ee.Date(str(year+step_range[1])+'-12-31')
        
            image = gee_data.composite(startDate, stopDate)
    
            # convert image to an RGB visualization
            images.append(image.visualize(**vis).copyProperties(image, image.propertyNames()))
            
        return images
    

    def export_images_as_geotiffs(self, geometry, start_year, stop_year, folder, dimensions=None):
        """
        Export video as GeoTIFF.
        ----------
        start_year : int
            First year  
        stop_year : int
            Last year
        dimensions : int
            A number or pair of numbers in format WIDTHxHEIGHT Maximum dimensions of the thumbnail to render, in pixels. 
            If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling.
        folder : str
            Path to the Drive folder to save the GeoTIFFs
        alpha_channel : Boolean
            If True adds transparency
        """
        # Area of Interest
        region = geometry.get('features')[0].get('geometry').get('coordinates')

        
        # Create ImageCollection
        images = self.create_collection(start_year, stop_year)
        
        # Export images as GeoTIFF
        tasks = {}
        for n, image in enumerate(images):
            image = ee.Image(image)

            if dimensions:
                task = ee.batch.Export.image.toDrive(image=image, description=f"{self.instrument}_{str(start_year+n)}", folder=folder,
                                                    fileNamePrefix=f"{self.instrument}_{str(start_year+n)}", 
                                                    dimensions=dimensions, crs='EPSG:3857', region=region, maxPixels = 1e13)
            else:
                task = ee.batch.Export.image.toDrive(image=image, description=f"{self.instrument}_{str(start_year+n)}", folder=folder,
                                                    fileNamePrefix=f"{self.instrument}_{str(start_year+n)}", 
                                                    crs='EPSG:3857', region=region, maxPixels = 1e13)
                
            task.start()

            tasks[f"{self.instrument}_{str(start_year+n)}"] = task

        # Wait for tasks to complete
        keys = list(tasks.keys())
        status_list = [tasks[key].status().get('state') for key in keys]

        while not status_list == ['COMPLETED'] * len(keys):
            status_list = [tasks[key].status().get('state') for key in keys]
            # Print temporal status
            tmp_status = dict(zip(keys, status_list))
            print('Temporal status: ', tmp_status)

            if any(status in ["FAILED", "CANCELLED"] for status in status_list):
                # print error message for each image
                for key in keys:
                    if tasks[key].status().get('state') in ["FAILED", "CANCELLED"]:
                        print(f"Error with image {key}: {tasks[key].status().get('error_message')}")

                # Cancel all tasks if one fails
                map(lambda key: tasks[key].cancel(), keys)
                
                break

            time.sleep(60)


        
    def video_as_array(self, geometry, start_year, stop_year, dimensions=None, alpha_channel=False):
        """
        Create Numpy array with 1 composite per year.
        ----------
        start_year : int
            First year
        stop_year : int
            Last year
        dimensions : int
            A number or pair of numbers in format WIDTHxHEIGHT Maximum dimensions of the thumbnail to render, in pixels. 
            If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling.
        alpha_channel : Boolean
            If True adds transparency
        """ 

        # Area of Interest
        region = geometry.get('features')[0].get('geometry').get('coordinates')
        polygon = ee.Geometry.Polygon(region)
        bounds = list(shape(geometry.get('features')[0].get('geometry')).bounds)
        
        images = self.create_collection(start_year, stop_year)
        
        for n, image in enumerate(images):
            print(f'Image number: {str(n)}')
            image = ee.Image(image)

            if dimensions:
                image =  image.reproject(crs='EPSG:4326', scale=self.scale)
                visSave = {'dimensions': dimensions, 'format': 'png', 'crs': 'EPSG:3857', 'region':region} 
            else:
                visSave = {'scale': self.scale,'region':region, 'crs': 'EPSG:3857'} 
    
            url = image.getThumbURL(visSave)
            response = requests.get(url)
            array = np.array(Image.open(io.BytesIO(response.content))) 
            
            array = array.reshape((1,) + array.shape)
            
            #Add alpha channel if needed
            if alpha_channel and array.shape[3] == 3:
                array = np.append(array, np.full((array.shape[0],array.shape[1], array.shape[2],1), 255), axis=3)
                if n == 0:
                    arrays = array[:,:,:,:4]
                else:
                    arrays = np.append(arrays, array[:,:,:,:4], axis=0)
            else:
                if n == 0:
                    arrays = array[:,:,:,:3]
                else:
                    arrays = np.append(arrays, array[:,:,:,:3], axis=0)
        
        return arrays
        
