import geopandas as gpd
from shapely.ops import unary_union

zip_path = "tariff_zones.zip"

#small skript to extract the tariff zones from PID
#Datasource: https://geoportalpraha.cz/en/data-and-services/d413927046764eb9a7ea61320a312635_0

gdf = gpd.read_file(f"zip://{zip_path}!DOP_PID_TARIFPASMA_P.shp")
gdf = gdf.to_crs(epsg=4326)
#print(gdf.info())
#print(gdf.columns)
#print(gdf.head())
#print(gdf.columns)
print(gdf['POPIS'].unique())
print(gdf.crs)
#zones of interest: See: https://pid.cz/en/tickets-and-fare/tariff-zones/
#we pick only the city of Prague: P is city, 0 is transfer through city, B is to city
zones_of_interest = ['P, 0, B']
filtered_zones = gdf[gdf['POPIS'].isin(zones_of_interest)]
union_polygon = unary_union(filtered_zones.geometry)
wkt_string = union_polygon.wkt
print(wkt_string)


with open("tariff_zones.wkt", "w") as file:
    file.write(wkt_string)



