import toml
from dataclasses import dataclass

import ee
import s3fs
import xarray as xr
import rioxarray
from dotenv import load_dotenv

# Take environment variables from .env
# Load the TOML file
with open('.env', 'r') as file:
    toml_data = file.read()
# Parse the TOML data
env_var = toml.loads(toml_data)


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


def read_ds():
    # Read Recent dataset
    dataset = 'global-dataset'
    group = 'recent'
    ds = read_zarr_from_s3(access_key_id=env_var["S3_ACCESS_KEY_ID"],
                           secret_accsess_key=env_var["S3_SECRET_ACCESS_KEY"],
                           dataset=dataset, group=group)
    ds = ds.drop_dims('depth').sel(time=['2000-12-31T00:00:00.000000000', '2018-12-31T00:00:00.000000000'])

    # Read land cover dataset
    dataset = 'land-cover'
    ds_lc = read_zarr_from_s3(access_key_id=env_var["S3_ACCESS_KEY_ID"],
                              secret_accsess_key=env_var["S3_SECRET_ACCESS_KEY"],
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