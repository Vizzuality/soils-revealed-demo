import datetime
from dataclasses import dataclass

import ee
import s3fs
import xarray as xr
import rioxarray
import numpy as np

NOW = datetime.datetime.now()


def read_zarr_from_s3(access_key_id, secret_accsess_key, dataset, group=None):
    # AWS S3 path
    s3_path = f's3://soils-revealed/{dataset}.zarr'

    # Initilize the S3 file system
    s3 = s3fs.S3FileSystem(key=access_key_id, secret=secret_accsess_key)
    store = s3fs.S3Map(root=s3_path, s3=s3, check=False)

    # Read Zarr file
    if group:
        ds = xr.open_zarr(store=store, group=group, consolidated=True)
    else:
        ds = xr.open_zarr(store=store, consolidated=True)

    return ds


def read_ds(access_key_id, secret_accsess_key):
    # Read Recent dataset
    dataset = 'global-dataset'
    group = 'recent'
    ds = read_zarr_from_s3(access_key_id=access_key_id,
                           secret_accsess_key=secret_accsess_key,
                           dataset=dataset, group=group)
    ds = ds.drop_dims('depth').sel(time=['2000-12-31T00:00:00.000000000', '2018-12-31T00:00:00.000000000'])

    # Read land cover dataset
    dataset = 'land-cover'
    ds_lc = read_zarr_from_s3(access_key_id=access_key_id,
                              secret_accsess_key=secret_accsess_key,
                              dataset=dataset)

    ds['land-cover'] = ds_lc['land-cover']

    return ds


@dataclass
class GEEData:
    dataset: str

    def image_collection_id(self):
        return {'Global-Land-Cover': 'projects/soils-revealed/ESA_landcover_ipcc',
                'SOC-Stock-Change': 'projects/soils-revealed/Recent/SOC_stocks'}[self.dataset]

    def ee_image(self, year='2018'):
        return {'Global-Land-Cover': ee.Image(ee.ImageCollection(self.image_collection_id()).
                                              filterDate(f'{year}-01-01', f'{year}-12-31').first()),
                'SOC-Stock-Change': ee.ImageCollection('projects/soils-revealed/Recent/SOC_stock_nov2020').filterDate(
                    '2018-01-01', '2018-12-31').first().subtract(
                    ee.ImageCollection('projects/soils-revealed/Recent/SOC_stock_nov2020').filterDate(
                        '2000-01-01', '2000-12-31').first())
                }[self.dataset]

    def sld_interval(self):
        return {'Global-Land-Cover': '<RasterSymbolizer>' + '<ColorMap type="values" extended="false">' +
                                     '<ColorMapEntry color="#ffff64" quantity="10" />' +
                                     '<ColorMapEntry color="#ffff64" quantity="11" />' +
                                     '<ColorMapEntry color="#ffff00" quantity="12" />' +
                                     '<ColorMapEntry color="#aaf0f0" quantity="20" />' +
                                     '<ColorMapEntry color="#dcf064" quantity="30" />' +
                                     '<ColorMapEntry color="#c8c864" quantity="40" />' +
                                     '<ColorMapEntry color="#006400" quantity="50" />' +
                                     '<ColorMapEntry color="#00a000" quantity="60" />' +
                                     '<ColorMapEntry color="#00a000" quantity="61" />' +
                                     '<ColorMapEntry color="#aac800" quantity="62" />' +
                                     '<ColorMapEntry color="#003c00" quantity="70" />' +
                                     '<ColorMapEntry color="#003c00" quantity="71" />' +
                                     '<ColorMapEntry color="#005000" quantity="72" />' +
                                     '<ColorMapEntry color="#285000" quantity="80" />' +
                                     '<ColorMapEntry color="#285000" quantity="81" />' +
                                     '<ColorMapEntry color="#286400" quantity="82" />' +
                                     '<ColorMapEntry color="#788200" quantity="90" />' +
                                     '<ColorMapEntry color="#8ca000" quantity="100" />' +
                                     '<ColorMapEntry color="#be9600" quantity="110" />' +
                                     '<ColorMapEntry color="#966400" quantity="120" />' +
                                     '<ColorMapEntry color="#966400" quantity="121" />' +
                                     '<ColorMapEntry color="#966400" quantity="122" />' +
                                     '<ColorMapEntry color="#ffb432" quantity="130" />' +
                                     '<ColorMapEntry color="#ffdcd2" quantity="140" />' +
                                     '<ColorMapEntry color="#ffebaf" quantity="150" />' +
                                     '<ColorMapEntry color="#ffc864" quantity="151" />' +
                                     '<ColorMapEntry color="#ffd278" quantity="152" />' +
                                     '<ColorMapEntry color="#ffebaf" quantity="153" />' +
                                     '<ColorMapEntry color="#00785a" quantity="160" />' +
                                     '<ColorMapEntry color="#009678" quantity="170" />' +
                                     '<ColorMapEntry color="#00dc82" quantity="180" />' +
                                     '<ColorMapEntry color="#c31400" quantity="190" />' +
                                     '<ColorMapEntry color="#fff5d7" quantity="200" />' +
                                     '<ColorMapEntry color="#dcdcdc" quantity="201" />' +
                                     '<ColorMapEntry color="#fff5d7" quantity="202" />' +
                                     '<ColorMapEntry color="#0046c8" quantity="210" opacity="0" />' +
                                     '<ColorMapEntry color="#ffffff" quantity="220" />' +
                                     '</ColorMap>' + '</RasterSymbolizer>',
                'SOC-Stock-Change': '<RasterSymbolizer>' + '<ColorMap extended="false" type="ramp">' +
                                    '<ColorMapEntry color="#B30200" quantity="-10"  opacity="1" />' +
                                    '<ColorMapEntry color="#E34A33" quantity="-7.5"  />' +
                                    '<ColorMapEntry color="#FC8D59" quantity="-5" />' +
                                    '<ColorMapEntry color="#FDCC8A" quantity="-2.5"  />' +
                                    '<ColorMapEntry color="#FFFFCC" quantity="0"  />' +
                                    '<ColorMapEntry color="#A1DAB4" quantity="2.5" />' +
                                    '<ColorMapEntry color="#31B3BD" quantity="5"  />' +
                                    '<ColorMapEntry color="#1C9099" quantity="7.5" />' +
                                    '<ColorMapEntry color="#066C59" quantity="10"  />' +
                                    '</ColorMap>' + '</RasterSymbolizer>'
                }[self.dataset]

    def class_colors(self):
        return {'Global-Land-Cover': {"10": "#ffff64", "11": "#ffff64", "12": "#ffff00", "20": "#aaf0f0",
                                      "30": "#dcf064", "40": "#c8c864", "50": "#006400", "60": "#00a000",
                                      "61": "#00a000", "62": "#aac800", "70": "#003c00", "71": "#003c00",
                                      "72": "#005000", "80": "#285000", "81": "#285000", "82": "#286400",
                                      "90": "#788200", "100": "#8ca000", "110": "#be9600", "120": "#966400",
                                      "121": "#966400", "122": "#966400", "130": "#ffb432", "140": "#ffdcd2",
                                      "150": "#ffebaf", "151": "#ffc864", "152": "#ffd278", "153": "#ffebaf",
                                      "160": "#00785a", "170": "#009678", "180": "#00dc82", "190": "#c31400",
                                      "200": "#fff5d7", "201": "#dcdcdc", "202": "#fff5d7", "210": "#0046c8",
                                      "220": "#ffffff"},
                'SOC-Stock-Change': {}
                }[self.dataset]

    def class_names(self):
        return {'Global-Land-Cover': {"10": "Cropland, rainfed",
                                      "11": "Cropland, rainfed, herbaceous cover",
                                      "12": "Cropland, rainfed, tree, or shrub cover",
                                      "20": "Cropland, irrigated or post-flooding",
                                      "30": "Mosaic cropland (>50%) / natural vegetation (tree, shrub, herbaceous cover) (<50%)",
                                      "40": "Mosaic natural vegetation (tree, shrub, herbaceous cover) (>50%) / cropland (<50%)",
                                      "50": "Tree cover, broadleaved, evergreen, closed to open (>15%)",
                                      "60": "Tree cover, broadleaved, deciduous, closed to open (>15%)",
                                      "61": "Tree cover, broadleaved, deciduous, closed (>40%)",
                                      "62": "Tree cover, broadleaved, deciduous, open (15- 40%)",
                                      "70": "Tree cover, needleleaved, evergreen, closed to open (>15%)",
                                      "71": "Tree cover, needleleaved, evergreen, closed (>40%)",
                                      "72": "Tree cover, needleleaved, evergreen, open (15-40%)",
                                      "80": "Tree cover, needleleaved, deciduous, closed to open (>15%)",
                                      "81": "Tree cover, needleleaved, deciduous, closed (>40%)",
                                      "82": "Tree cover, needleleaved, deciduous, open (15-40%)",
                                      "90": "Tree cover, mixed leaf type (broadleaved and needleleaved)",
                                      "100": "Mosaic tree and shrub (>50%) / herbaceous cover (<50%)",
                                      "110": "Mosaic herbaceous cover (>50%) / tree and shrub (<50%)",
                                      "120": "Shrubland",
                                      "121": "Evergreen shrubland",
                                      "122": "Deciduous shrubland",
                                      "130": "Grassland",
                                      "140": "Lichens and mosses",
                                      "150": "Sparse vegetation (tree, shrub, herbaceous cover) (<15%)",
                                      "151": "Sparse tree (<15%)",
                                      "152": "Sparse shrub (<15%)",
                                      "153": "Sparse herbaceous cover (<15%)",
                                      "160": "Tree cover, flooded, fresh, or brackish water",
                                      "170": "Tree cover, flooded, saline water",
                                      "180": "Shrub or herbaceous cover, flooded, fresh/saline/brackish water",
                                      "190": "Urban areas",
                                      "200": "Bare areas ",
                                      "201": "Consolidated bare areas",
                                      "202": "Unconsolidated bare areas",
                                      "210": "Water bodies",
                                      "220": "Permanent snow and ice "},
                'SOC-Stock-Change': {}
                }[self.dataset]

    def class_group_names(self):
        return {'Global-Land-Cover': {"0": "No Data",
                                      "10": "Cropland",
                                      "11": "Cropland",
                                      "12": "Cropland",
                                      "20": "Cropland",
                                      "30": "Cropland",
                                      "40": "Cropland",
                                      "50": "Tree cover",
                                      "60": "Tree cover",
                                      "61": "Tree cover",
                                      "62": "Tree cover",
                                      "70": "Tree cover",
                                      "71": "Tree cover",
                                      "72": "Tree cover",
                                      "80": "Tree cover",
                                      "81": "Tree cover",
                                      "82": "Tree cover",
                                      "90": "Tree cover",
                                      "100": "Shrubland",
                                      "110": "Shrubland",
                                      "120": "Shrubland",
                                      "121": "Shrubland",
                                      "122": "Shrubland",
                                      "130": "Grassland",
                                      "140": "Lichens and mosses",
                                      "150": "Sparse vegetation",
                                      "152": "Sparse vegetation",
                                      "153": "Sparse vegetation",
                                      "160": "Flooded areas",
                                      "170": "Flooded areas",
                                      "180": "Flooded areas",
                                      "190": "Urban areas",
                                      "200": "Bare areas",
                                      "201": "Bare areas",
                                      "202": "Bare areas",
                                      "210": "Water bodies",
                                      "220": "Snow and ice"},
                'SOC-Stock-Change': {}
                }[self.dataset]

    def class_group_colors(self):
        return {'Global-Land-Cover': {"No Data": "#ffffff",
                                      "Cropland": "#ffff64",
                                      "Tree cover": "#003c00",
                                      "Shrubland": "#966400",
                                      "Grassland": "#ffb432",
                                      "Lichens and mosses": "#ffdcd2",
                                      "Sparse vegetation": "#ffebaf",
                                      "Flooded areas": "#009678",
                                      "Urban areas": "#c31400",
                                      "Bare areas": "#fff5d7",
                                      "Water bodies": "#0046c8",
                                      "Snow and ice": "#ffffff"
                                      },
                'SOC-Stock-Change': {}
                }[self.dataset]
    
@dataclass
class SatelliteImageryData:
    dataset: str = None
    instrument: str = None

    @property
    def collections(self):
        return {
            'Sentinel-2-Top-of-Atmosphere-Reflectance': 'COPERNICUS/S2',
            'Landsat-4-Surface-Reflectance': 'LANDSAT/LT04/C01/T1_SR',
            'Landsat-5-Surface-Reflectance': 'LANDSAT/LT05/C01/T1_SR',
            'Landsat-7-Surface-Reflectance': 'LANDSAT/LE07/C01/T1_SR',
            'Landsat-8-Surface-Reflectance': 'LANDSAT/LC08/C01/T1_SR',
            'Landsat-457-Surface-Reflectance': ['LANDSAT/LT04/C01/T1_SR','LANDSAT/LT05/C01/T1_SR', 'LANDSAT/LE07/C01/T1_SR']
            }[self.dataset]
    
    @property
    def bands(self):
        return {
            'Sentinel-2-Top-of-Atmosphere-Reflectance': ['B1','B2','B3','B4','B5','B6','B7','B8A','B8','B11','B12','NDVI','NDWI'],
            'Landsat-4-Surface-Reflectance': ['B1','B2','B3','B4','B5','B6','B7','NDVI','NDWI'],
            'Landsat-5-Surface-Reflectance': ['B1','B2','B3','B4','B5','B6','B7','NDVI','NDWI'],
            'Landsat-7-Surface-Reflectance': ['B1','B2','B3','B4','B5','B6','B7','NDVI','NDWI'],
            'Landsat-457-Surface-Reflectance': ['B1','B2','B3','B4','B5','B6','B7','NDVI','NDWI'],
            'Landsat-8-Surface-Reflectance': ['B1','B2','B3','B4','B5','B6','B7','B10','B11','NDVI','NDWI'],
            }[self.dataset]
    
    @property
    def rgb_bands(self):
        return {
            'Sentinel-2-Top-of-Atmosphere-Reflectance': ['B4','B3','B2'],
            'Landsat-4-Surface-Reflectance': ['B3','B2','B1'],
            'Landsat-5-Surface-Reflectance': ['B3','B2','B1'],
            'Landsat-7-Surface-Reflectance': ['B3','B2','B1'],
            'Landsat-457-Surface-Reflectance': ['B3','B2','B1'],
            'Landsat-8-Surface-Reflectance': ['B4', 'B3', 'B2']
            }[self.dataset]
    
    @property
    def band_names(self):
        return {
            'Sentinel-2-Top-of-Atmosphere-Reflectance': ['RGB','NDVI', 'NDWI'],
            'Landsat-4-Surface-Reflectance': ['RGB','NDVI', 'NDWI'],
            'Landsat-5-Surface-Reflectance': ['RGB','NDVI', 'NDWI'],
            'Landsat-7-Surface-Reflectance': ['RGB','NDVI', 'NDWI'],
            'Landsat-457-Surface-Reflectance': ['RGB','NDVI', 'NDWI'],        
            'Landsat-8-Surface-Reflectance': ['RGB','NDVI', 'NDWI']
            }[self.dataset]
    
    @property
    def scale(self):
        return {
            'Sentinel-2-Top-of-Atmosphere-Reflectance': 10,
            'Landsat-4-Surface-Reflectance': 30,
            'Landsat-5-Surface-Reflectance': 30,
            'Landsat-7-Surface-Reflectance': 30,
            'Landsat-457-Surface-Reflectance': 30,        
            'Landsat-8-Surface-Reflectance': 30
            }[self.dataset]
    
    @property
    def vizz_params_rgb(self):
        return {
            'Sentinel-2-Top-of-Atmosphere-Reflectance': {'min':100,'max':2500, 'bands':['B4','B3','B2']},
            'Landsat-4-Surface-Reflectance': {'min':100,'max':2500, 'gamma':1.4, 'bands':['B3','B2','B1']},
            'Landsat-5-Surface-Reflectance': {'min':100,'max':2500, 'gamma':1.4, 'bands':['B3','B2','B1']},
            'Landsat-7-Surface-Reflectance': {'min':100,'max':2500, 'gamma':1.4, 'bands':['B3','B2','B1']},
            'Landsat-457-Surface-Reflectance': {'min':100,'max':2500, 'gamma':1.4, 'bands':['B3','B2','B1']},
            'Landsat-8-Surface-Reflectance': {'min':100,'max':2500, 'gamma':1.4, 'bands':['B4','B3','B2']}
            }[self.dataset]
    
    @property
    def vizz_params(self):
        return {
            'Sentinel-2-Top-of-Atmosphere-Reflectance': [{'min':0,'max':3000, 'bands':['B4','B3','B2']},
                {'min':-1,'max':1, 'bands':['NDVI']},
                {'min':-1,'max':1, 'bands':['NDWI']}],
            'Landsat-4-Surface-Reflectance': [{'min':0,'max':3000, 'gamma':1.4, 'bands':['B3','B2','B1']},
                {'min':-1,'max':1, 'gamma':1.4, 'bands':['NDVI']},
                {'min':-1,'max':1, 'gamma':1.4, 'bands':['NDWI']}],
            'Landsat-5-Surface-Reflectance': [{'min':0,'max':3000, 'gamma':1.4, 'bands':['B3','B2','B1']},
                {'min':-1,'max':1, 'gamma':1.4, 'bands':['NDVI']},
                {'min':-1,'max':1, 'gamma':1.4, 'bands':['NDWI']}],
            'Landsat-7-Surface-Reflectance': [{'min':0,'max':3000, 'gamma':1.4, 'bands':['B3','B2','B1']},
                {'min':-1,'max':1, 'gamma':1.4, 'bands':['NDVI']},
                {'min':-1,'max':1, 'gamma':1.4, 'bands':['NDWI']}],
            'Landsat-457-Surface-Reflectance': [{'min':0,'max':3000, 'gamma':1.4, 'bands':['B3','B2','B1']},
                {'min':-1,'max':1, 'gamma':1.4, 'bands':['NDVI']},
                {'min':-1,'max':1, 'gamma':1.4, 'bands':['NDWI']}],        
            'Landsat-8-Surface-Reflectance': [{'min':0,'max':3000, 'gamma':1.4, 'bands':['B4','B3','B2']},
                {'min':-1,'max':1, 'gamma':1.4, 'bands':['NDVI']},
                {'min':-1,'max':1, 'gamma':1.4, 'bands':['NDWI']}]
            }[self.dataset]
    
    @property
    def time_steps(self):
        return {
            'Sentinel-2-Top-of-Atmosphere-Reflectance': 1,
            'Landsat-457-Surface-Reflectance': 4,
            'Landsat-8-Surface-Reflectance': 1
            }[self.dataset]
    
    @property
    def step_range(self):
        """
        Composite years time step ranges
        """
        return {
            'Sentinel-2-Top-of-Atmosphere-Reflectance': [-1,0],
            'Landsat-457-Surface-Reflectance': [-2,2],
            'Landsat-8-Surface-Reflectance': [-1,0],
        }[self.dataset]
    
    
    @property
    def date_range(self):
        return {
            'Landsat': {'Landsat-457-Surface-Reflectance': np.arange(1985, 2012+1), 'Landsat-8-Surface-Reflectance': np.arange(2013, NOW.year)},
            'Sentinel': {'Sentinel-2-Top-of-Atmosphere-Reflectance': np.arange(2016, NOW.year)}
            }[self.instrument]
    
    @property
    def composite(self):
        return {
            'Sentinel-2-Top-of-Atmosphere-Reflectance': CloudFreeCompositeS2,
            'Landsat-4-Surface-Reflectance': CloudFreeCompositeL,
            'Landsat-5-Surface-Reflectance': CloudFreeCompositeL,
            'Landsat-7-Surface-Reflectance': CloudFreeCompositeL7,
            'Landsat-457-Surface-Reflectance': CloudFreeCompositeL457,
            'Landsat-8-Surface-Reflectance': CloudFreeCompositeL8
            }[self.dataset]
    

## ------------------------- Filter datasets ------------------------- ##
## Lansat 4, 5 and 7 Cloud Free Composite
def CloudMaskL457(image):
    qa = image.select('pixel_qa')
    #If the cloud bit (5) is set and the cloud confidence (7) is high
    #or the cloud shadow bit is set (3), then it's a bad pixel.
    cloud = qa.bitwiseAnd(1 << 5).And(qa.bitwiseAnd(1 << 7)).Or(qa.bitwiseAnd(1 << 3))
    #Remove edge pixels that don't occur in all bands
    mask2 = image.mask().reduce(ee.Reducer.min())
    return image.updateMask(cloud.Not()).updateMask(mask2)

def CloudFreeCompositeL(Collection_id, startDate, stopDate):
    ## Define your collection
    collection = ee.ImageCollection(Collection_id)

    ## Filter 
    collection = collection.filterDate(startDate,stopDate)\
            .map(CloudMaskL457)

    ## Composite
    composite = collection.median()
    
    return composite

## Lansat 4 Cloud Free Composite
def CloudFreeCompositeL4(startDate, stopDate):
    ## Define your collections
    collection_L4 = ee.ImageCollection('LANDSAT/LT04/C01/T1_SR')

    ## Filter 
    collection_L4 = collection_L4.filterDate(startDate,stopDate).map(CloudMaskL457)

    ## Composite
    composite = collection_L4.median()
    
    return composite

## Lansat 5 Cloud Free Composite
def CloudFreeCompositeL5(startDate, stopDate):
    ## Define your collections
    collection_L5 = ee.ImageCollection('LANDSAT/LT05/C01/T1_SR')

    ## Filter 
    collection_L5 = collection_L5.filterDate(startDate,stopDate).map(CloudMaskL457)

    ## Composite
    composite = collectionL5.median()
    
    return composite

## Lansat 4 + 5 + 7 Cloud Free Composite
def CloudFreeCompositeL457(startDate, stopDate):
    ## Define your collections
    collection_L4 = ee.ImageCollection('LANDSAT/LT04/C01/T1_SR')
    collection_L5 = ee.ImageCollection('LANDSAT/LT05/C01/T1_SR')
    collection_L7 = ee.ImageCollection('LANDSAT/LE07/C01/T1_SR')

    ## Filter 
    collection_L4 = collection_L4.filterDate(startDate,stopDate).map(CloudMaskL457)
    collection_L5 = collection_L5.filterDate(startDate,stopDate).map(CloudMaskL457)
    collection_L7 = collection_L7.filterDate(startDate,stopDate).map(CloudMaskL457)
    
    ## merge collections
    collection = collection_L4.merge(collection_L5).merge(collection_L7)

    ## Composite
    composite = collection.median()
    
    return composite

## Lansat 7 Cloud Free Composite
def CloudMaskL7sr(image):
    qa = image.select('pixel_qa')
    #If the cloud bit (5) is set and the cloud confidence (7) is high
    #or the cloud shadow bit is set (3), then it's a bad pixel.
    cloud = qa.bitwiseAnd(1 << 5).And(qa.bitwiseAnd(1 << 7)).Or(qa.bitwiseAnd(1 << 3))
    #Remove edge pixels that don't occur in all bands
    mask2 = image.mask().reduce(ee.Reducer.min())
    return image.updateMask(cloud.Not()).updateMask(mask2)

def CloudFreeCompositeL7(startDate, stopDate):
    ## Define your collection
    collection = ee.ImageCollection('LANDSAT/LE07/C01/T1_SR')

    ## Filter 
    collection = collection.filterDate(startDate,stopDate).map(CloudMaskL7sr)

    ## Composite
    composite = collection.median()
    
    ## normDiff bands
    normDiff_band_names = ['NDVI', 'NDWI']
    for nB, normDiff_band in enumerate([['B4','B3'], ['B4','B2']]):
        image_nd = composite.normalizedDifference(normDiff_band).rename(normDiff_band_names[nB])
        composite = ee.Image.cat([composite, image_nd])
    
    return composite

## Lansat 8 Cloud Free Composite
def CloudMaskL8sr(image):
    opticalBands = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']
    thermalBands = ['B10', 'B11']

    cloudShadowBitMask = ee.Number(2).pow(3).int()
    cloudsBitMask = ee.Number(2).pow(5).int()
    qa = image.select('pixel_qa')
    mask1 = qa.bitwiseAnd(cloudShadowBitMask).eq(0).And(
    qa.bitwiseAnd(cloudsBitMask).eq(0))
    mask2 = image.mask().reduce('min')
    mask3 = image.select(opticalBands).gt(0).And(
            image.select(opticalBands).lt(10000)).reduce('min')
    mask = mask1.And(mask2).And(mask3)
    
    return image.updateMask(mask)

def CloudFreeCompositeL8(startDate, stopDate):
    ## Define your collection
    collection = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR')

    ## Filter 
    collection = collection.filterDate(startDate,stopDate).map(CloudMaskL8sr)

    ## Composite
    composite = collection.median()
    
    ## normDiff bands
    normDiff_band_names = ['NDVI', 'NDWI']
    for nB, normDiff_band in enumerate([['B5','B4'], ['B5','B3']]):
        image_nd = composite.normalizedDifference(normDiff_band).rename(normDiff_band_names[nB])
        composite = ee.Image.cat([composite, image_nd])
    
    return composite

## Sentinel 2 Cloud Free Composite
def CloudMaskS2(image):
    """
    European Space Agency (ESA) clouds from 'QA60', i.e. Quality Assessment band at 60m
    parsed by Nick Clinton
    """
    AerosolsBands = ['B1']
    VIBands = ['B2', 'B3', 'B4']
    RedBands = ['B5', 'B6', 'B7', 'B8A']
    NIRBands = ['B8']
    SWIRBands = ['B11', 'B12']

    qa = image.select('QA60')

    # Bits 10 and 11 are clouds and cirrus, respectively.
    cloudBitMask = int(2**10)
    cirrusBitMask = int(2**11)

    # Both flags set to zero indicates clear conditions.
    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(\
            qa.bitwiseAnd(cirrusBitMask).eq(0))

    return image.updateMask(mask)

def CloudFreeCompositeS2(startDate, stopDate):
    ## Define your collection
    collection = ee.ImageCollection('COPERNICUS/S2')

    ## Filter 
    collection = collection.filterDate(startDate,stopDate)\
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))\
            .map(CloudMaskS2)

    ## Composite
    composite = collection.median()
    
    ## normDiff bands
    normDiff_band_names = ['NDVI', 'NDWI']
    for nB, normDiff_band in enumerate([['B8','B4'], ['B8','B3']]):
        image_nd = composite.normalizedDifference(normDiff_band).rename(normDiff_band_names[nB])
        composite = ee.Image.cat([composite, image_nd])
    
    return composite


## ------------------------------------------------------------------- ##