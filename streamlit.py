import streamlit as st
import pandas as pd
import mysql.connector
from datetime import date

conn=mysql.connector.connect(
    host="localhost",
    user="root",
    password="25Mysql@",
    database="neo"
)

def execute_query(query):
    cursor=conn.cursor()
    cursor.execute(query)
    result=cursor.fetchall()
    columns=[desc[0] for desc in cursor.description]
    cursor.close()
    return pd.DataFrame(result,columns=columns)
st.set_page_config(
    page_title="Asteroids Dashboard"
)
st.title("NASA Asteroids tracker")
page=st.sidebar.radio("Asteroid Approaches",("Queries","Filters"))

queries={
    "1.Approach count of all asteroids":
        "SELECT neo_reference_id,COUNT(*) AS approach_count from close_approach group by neo_reference_id",
    
    "2.Average velocity of each asteroid":
        "SELECT neo_reference_id,AVG(relative_velocity_kmph) AS average_velocity from close_approach group by neo_reference_id",
    
    "3. List of top 10 fastest asteroids":
        "SELECT a.name,c.neo_reference_id,max(c.relative_velocity_kmph) as max_velocity from asteroids a join close_approach c on a.id=c.neo_reference_id group by a.name,a.id order by max_velocity desc limit 10",
    
    "4. Find potentially hazardous asteroids that have approached Earth more than 3 times":
        "SELECT a.name,a.id,count(*) as approach_count from asteroids a join close_approach c on a.id=c.neo_reference_id where a.is_potentially_hazardous_asteroid = 1 group by a.name,a.id having approach_count>3",
    
    "5. Find the month with the most asteroid approaches ":
        "SELECT MONTH(close_approach_date) as month , count(*) as total_approaches from close_approach group by month(close_approach_date) order by total_approaches desc limit 1",
    "6. Asteroid with the fastest ever approach speed ":
        "SELECT a.name,c.neo_reference_id,relative_velocity_kmph from asteroids a join close_approach c on a.id=c.neo_reference_id order by relative_velocity_kmph desc limit 1",
    "7. Sort asteroids by maximum estimated diameter (descending)":
        "SELECT name,id,estimated_diameter_max_km from asteroids order by estimated_diameter_max_km desc",
    "8. An asteroid whose closest approach is getting nearer over time":
        """select *from (
        select neo_reference_id,close_approach_date,miss_distance_km, LAG(miss_distance_km) over (partition by neo_reference_id order by close_approach_date) as previous_distance from close_approach
        ) as subquery where miss_distance_km<previous_distance
        """,
    "9. Display the name of each asteroid along with the date and miss distance of its closest approach to Earth. ":
        "SELECT a.name,c.miss_distance_km,c.close_approach_date from asteroids a join close_approach c on a.id=c.neo_reference_id WHERE (c.neo_reference_id, c.miss_distance_km) IN (SELECT  neo_reference_id,  MIN(miss_distance_km) FROM close_approach GROUP BY neo_reference_id)",
    "10. List names of asteroids that approached Earth with velocity > 50,000 km/h":
        "SELECT DISTINCT a.name, c.relative_velocity_kmph from close_approach c join asteroids a on c.neo_reference_id = a.id where c.relative_velocity_kmph > 50000",
    "11. Count how many approaches happened per month ":
        "SELECT MONTH(close_approach_date) as month_number , count(*) as total_approaches from close_approach group by  MONTH(close_approach_date) order by  MONTH(close_approach_date)",
    
    "12. Find asteroid with the highest brightness (lowest magnitude value) ":
        "SELECT id, name, absolute_magnitude_h from asteroids order by absolute_magnitude_h asc limit 1",
    
    "13. Get number of hazardous vs non-hazardous asteroids ":
        "SELECT is_potentially_hazardous_asteroid, count(*) AS count FROM asteroids group by is_potentially_hazardous_asteroid",
    
    "14. Find asteroids that passed closer than the Moon (lesser than 1 LD), along with their close approach date and distance. ":
        "SELECT c.neo_reference_id, a.name,c.close_approach_date,c.miss_distance_lunar from asteroids a join close_approach c on a.id=c.neo_reference_id where c.miss_distance_lunar<1",
    
    "15. Find asteroids that came within 0.05 AU(astronomical distance)":
        "SELECT c.neo_reference_id,a.name,c.close_approach_date,c.astronomical from asteroids a join close_approach c on a.id=c.neo_reference_id where c.astronomical<0.05",
    "16. Asteroid with the greatest miss distance":
        "select a.name,a.id,c.miss_distance_km from asteroids a join close_approach c on a.id= c.neo_reference_id order by miss_distance_km desc limit 1",
    "17.Find the average estimated diameter(in km) of hazardous asteroids":
        "SELECT round(avg((estimated_diameter_min_km + estimated_diameter_max_km)),3) as average_estm_diameter from asteroids where is_potentially_hazardous_asteroid=1",
    "18. Shortest miss distance of hazardous asteroid":
        "SELECT a.name,c.close_approach_date,c.miss_distance_km from asteroids a join close_approach c on a.id=c.neo_reference_id  order by a.id asc limit 1",
    "19. Asteroids with Diameter > 1 km":
        "SELECT id,name,estimated_diameter_max_km from asteroids where estimated_diameter_max_km>1 order by estimated_diameter_max_km desc",
    "20. Total number of unique asteroids that have approached Earth":
        "SELECT count(distinct neo_reference_id) as unique_approaches from close_approach where orbiting_body='Earth'"
}

if page=="Queries":
    st.header("Pre-defined Queries")
    selected=st.selectbox("Select a query to run:",list(queries.keys()))
    df=execute_query(queries[selected])
    st.dataframe(df)

elif page=="Filters":
    st.subheader("Customize your search")

    date_range = st.sidebar.date_input("Close Approach Date Range", [date(2024, 1, 1), date(2025, 6, 6)])
    
    au_range = st.sidebar.slider("Astronomical Distance (AU)", 0.0, 0.5, (0.0, 0.5), 0.01)
    ld_range = st.sidebar.slider("Lunar Distance (LD)", 0.0, 100.0, (0.0, 100.0), 0.5)
    velocity_range = st.sidebar.slider("Relative Velocity (km/h)", 1410, 180000, (1410, 180000),10)
    
    max_diameter_range = st.sidebar.slider("Estimated Diameter Max (km)", 0.0, 11.0, (0.0, 11.0), 0.1)
    min_diameter_range = st.sidebar.slider("Estimated Diameter Min (km)", 0.0, 5.0, (0.0, 5.0), 0.1)
    hazardous = st.sidebar.selectbox("Show Only Hazardous Asteroids?", ["All","Yes", "No"])

    filters = [
        f"c.close_approach_date BETWEEN '{date_range[0]}' AND '{date_range[1]}'",
        f"c.astronomical BETWEEN {au_range[0]} AND {au_range[1]}",
        f"c.miss_distance_lunar BETWEEN {ld_range[0]} AND {ld_range[1]}",
        f"c.relative_velocity_kmph BETWEEN {velocity_range[0]} AND {velocity_range[1]}",
       
        f"a.estimated_diameter_max_km BETWEEN {max_diameter_range[0]} AND {max_diameter_range[1]}",
        f"a.estimated_diameter_min_km BETWEEN {min_diameter_range[0]} AND {min_diameter_range[1]}"
    ]

    if hazardous == "Yes":
        filters.append("a.is_potentially_hazardous_asteroid = TRUE")
    elif hazardous=="No":
        filters.append("a.is_potentially_hazardous_asteroid = FALSE")


    filter_query = f"""
    SELECT a.id, a.name, c.close_approach_date, c.relative_velocity_kmph,
           c.astronomical, c.miss_distance_km, c.miss_distance_lunar,c.orbiting_body,a.absolute_magnitude_h,
           a.estimated_diameter_min_km,a.estimated_diameter_max_km ,
           a.is_potentially_hazardous_asteroid
    FROM close_approach as c
    JOIN asteroids a ON c.neo_reference_id = a.id
    WHERE {' AND '.join(filters)}
    ORDER BY c.close_approach_date
    """

    filtered_df = execute_query(filter_query)
    st.dataframe(filtered_df)
    
