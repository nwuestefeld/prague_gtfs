"""
shape.py: Extract tariff zone polygons from a PID shapefile and save as WKT.

Reads 'DOP_PID_TARIFPASMA_P.shp' from a zip archive, filters for zone 'P',
creates a unified polygon, and writes the result to 'tariff_zones.wkt'.
"""
import geopandas as gpd
from shapely.ops import unary_union

def main():
    """Extract tariff zone polygons from a PID shapefile and save as WKT."""
    zip_path = "tariff_zones.zip"

    # Read shapefile from zip
    gdf = gpd.read_file(f"zip://{zip_path}!DOP_PID_TARIFPASMA_P.shp")
    gdf = gdf.to_crs(epsg=4326)

    # Filter for city zone “P”
    filtered_zones = gdf[
        gdf['POPIS'].str.contains(r'\bP\b', regex=True, na=False)
    ]
    union_polygon = unary_union(filtered_zones.geometry)
    wkt_string = union_polygon.wkt

    # Write to file
    with open("tariff_zones.wkt", "w") as file:
        file.write(wkt_string)

if __name__ == "__main__":
    main()
