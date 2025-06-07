import sqlite3

conn = sqlite3.connect("vehicle_positions.db")
cursor = conn.cursor()

query = """
SELECT gtfs_trip_id, vehicle_id, delay, timestamp
FROM vehicle_positions
WHERE DATE(timestamp) = '2025-06-0';
"""

cursor.execute(query)
results = cursor.fetchall()

if results:
    for row in results:
        print(row)
else:
    print("Keine Einträge für den 19.05.2025 gefunden.")

conn.close()

  query = (
    "SELECT gtfs_trip_id, vehicle_id, route_type, gtfs_route_short_name, "
    "AVG(delay) AS delay, MIN(timestamp) AS first_timestamp "
    "FROM vehicle_positions "
    "WHERE delay IS NOT NULL "
    f"AND longitude BETWEEN {minx} AND {maxx} "
    f"AND latitude BETWEEN {miny} AND {maxy} "
    f"AND delay BETWEEN {min_delay} AND 7200 "
    f"AND DATE(timestamp) = '2025-05-21' "
    "GROUP BY gtfs_trip_id"
)
