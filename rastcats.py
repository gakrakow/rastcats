from rasterstats import zonal_stats
from fiona import open as fopen
from csv import DictWriter
from sys import argv, exit
from os.path import expanduser, splitext, dirname
from yaml import load, safe_dump
from Tkinter import Tk()
from tkFileDialog import askopenfilename, asksaveasfilename
from rasterio import _err, coords, enums, vfs, sample

# Import Yaml settings file into key word dictionary called conf. 
# Yaml file needs to be same name (with .yml extension instead of .py) and 
# in same folder as currently executing python file.
yaml_file = splitext(argv[0])[0] + '.yml'
conf = load(open(yaml_file, 'r').read())

# Get field names of input raster categories
category_map = conf['category_map']
rst_fields = category_map.values()

# Do not show parent Tk dialog
root = Tk()
root.withdraw()

#create dictionary for file dialog options
file_opt = {}

# Choose vector overlay file
vector_filename = conf['vector_overlay_path']
file_opt['title'] = 'Please select the polygon overlay ESRI shapefile'
file_opt['filetypes'] = [("ESRI shapefiles", ".shp")] # Add other vector formats that work here.
file_opt['initialdir'] = default=expanduser(vector_filename)
vector_filename = askopenfilename(**file_opt)
if vector_filename == '': 
    print('Exiting - user cancelation')
    exit()
# Replace path in conf dict using file selected by user.
conf['vector_overlay_path'] = dirname(abspath(vector_filename)) + '\\'

### Get raster category file (most likely land cover data)###
raster_filename = conf['raster_categories_path']
file_opt['title'] = 'Please select the raster category overlay file'
file_opt['filetypes'] = [("Raster Image File", ".img")] # Add other raster formats that work here.
file_opt['initialdir'] = expanduser(raster_filename)
raster_filename = askopenfilename(**file_opt)
if raster_filename == '':
    print('Exiting - user cancelation')
    exit()
# Replace path in conf dict using file selected by user.
conf['raster_categories_path'] = dirname(abspath(raster_filename)) + '\\'

### Choose csv output file ###
csv_filename = conf['csv_output_path']
file_opt['title'] = 'Please select the csv output file'
file_opt['filetypes'] = [('csv files', '.csv')]
file_opt['initialdir'] = expanduser(csv_filename)
csv_filename = asksaveasfilename(**file_opt)
if csv_filename == '':
    print('No csv file name selected')
    exit()

### Dump the paths to yaml file on disk ###
safe_dump(conf, file(yaml_file,'w'), encoding='utf-8', allow_unicode=True, default_flow_style=False)


# Open shapefile using Fiona
with fopen(vector_filename, 'r') as vct:
      
    # Get field names of input vector layer
    vct_fields = []
    feat = vct[0]
    for fld in feat['properties']:
        vct_fields.append(fld)
    
    # Merge field name lists
    fieldnames = vct_fields + rst_fields

    with open(csv_filename, 'wb') as csvfile:
        # Start writing csv and add attribute names for first row
        writer = DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Get values from vector feature and selected pixel values of from raster image
        for vct_feat in vct:
            vct_val_dict = dict(vct_feat['properties'])
            rst_val_dict = zonal_stats(vct_feat, raster_filename, categorical=True, copy_properties=True, category_map=category_map, nodata = -999)[0]
            rowvalues = dict(vct_val_dict.items() + rst_val_dict.items())
            # Write row to csv file
            writer.writerow(rowvalues)
