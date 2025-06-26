"""
Python script that allows the user to run the sql queries and view the results in a pandas dataframe if that is preferred over a database management system like dbeaver

Some queries were created with some insiration from DataLemur. I have spent tons of time on that website practicing SQL skills, and wanted to replicate some of those questions here.
Most queries were created with the intention of using a cte or window function.
"""

import sqlite3
import pandas as pd

# Connect to the SQLite database
con = sqlite3.connect('users.db')
cur = con.cursor()

# 1. Return users (all fields) who have an actual age that is above the average for the users actual country fpr the entire dataset.
print("\n1. Return users (all fields) who have an actual age that is above the average for the users actual country fpr the entire dataset. \n")
first_query = f"""
WITH country_avg_age AS (
	SELECT 
		users_data.country,
		ROUND(AVG(users_data.age), 2) AS avg_age
	FROM users_names_data users_data
	GROUP BY users_data.country
),

add_avg_age AS (
	SELECT 
		users_data.*,
		avg_age_cte.avg_age
	FROM users_names_data users_data
	JOIN country_avg_age avg_age_cte -- more efficient than left join bc we only want records that match
		ON users_data.country = avg_age_cte.country
)

SELECT *
FROM add_avg_age
WHERE 1=1
	AND (age > avg_age)
"""
first_result_df = pd.read_sql_query(first_query, con)
print(first_result_df)



# 2. Return a histogram of distinct first names per state. AKA group the states by number of distinct names
print("\n2. Return a histogram of distinct first names per state. AKA group the states by number of distinct names. \n")
second_query = f"""
WITH num_distinct_first_names AS (
	SELECT 
		users_data.state,
		COUNT(DISTINCT users_data.first_name) AS num_dist_first_names
	FROM users_names_data users_data
	GROUP BY users_data.state
)

SELECT
	num_distinct_first_names.num_dist_first_names,
	COUNT(DISTINCT num_distinct_first_names.state) AS states_num
FROM num_distinct_first_names
GROUP BY num_distinct_first_names.num_dist_first_names

"""
second_result_df = pd.read_sql_query(second_query, con)
print(second_result_df)



# 3. Return the top 50 names, age, predicted age, city, state, postal code, and country of the users with the largest gap in absolute value of (age - predicted age)
print("\n3. Return the top 50 names, age, predicted age, city, state, postal code, and country of the users with the largest gap in absolute value of (age - predicted age). \n")
third_query = f"""
SELECT 
	users_data.first_name,
	users_data.last_name,
	users_data.age,
	users_data.city,
	users_data.state,
	users_data.postcode,
	users_data.country,
	users_data.agify_predicted_age,
	COALESCE(abs(users_data.age - users_data.agify_predicted_age), 0) as predicted_age_differece -- coalesce because we dont want to include nulls and we also dont want to include same predicated age & age, so perfect use case for this
FROM users_names_data users_data
WHERE COALESCE(abs(users_data.age - users_data.agify_predicted_age), 0) > 0
ORDER BY predicted_age_differece DESC
LIMIT 50
"""
third_result_df = pd.read_sql_query(third_query, con)
print(third_result_df)




# 4. Write a query to determine the most common birth month by country. Using at least 1 cte to answer this question
print("\n4. Write a query to determine the most common birth month by country. Using at least 1 cte to answer this question. \n")
fourth_query = f"""
WITH num_birth_months_per_country AS (
	SELECT
		*,
--		COUNT(*) OVER (PARTITION BY country, MONTH(users_data.birth_date)) AS num --Not allowed in sqlite. Is allowed in sqlserver.
		COUNT(*) OVER (PARTITION BY country, strftime('%m', birth_date)) AS num 
	FROM users_names_data users_data
),

add_rank AS (
	SELECT 
		births_per_country.*,
		ROW_NUMBER() OVER (PARTITION BY births_per_country.country ORDER BY num DESC) AS rank_num
	FROM num_birth_months_per_country births_per_country
)

SELECT
	add_rank_cte.country,
	strftime('%m', add_rank_cte.birth_date) as birth_month,
	add_rank_cte.num
FROM add_rank add_rank_cte
WHERE rank_num = 1
"""
fourth_result_df = pd.read_sql_query(fourth_query, con)
print(fourth_result_df)


# 5. Write a query to return the 2rd highest age (maybe could do predicted age with a full dataset) by nationality
print("\n5. Write a query to return the 2rd highest age (maybe could do predicted age with a full dataset) by nationality. \n")
fifth_query = f"""
WITH ranked_age AS (
	SELECT 
		*,
		RANK() OVER (PARTITION BY users_data.nationality ORDER BY users_data.age DESC) AS age_rank
	FROM users_names_data users_data
	ORDER BY nationality
)

SELECT
	ranked_age.nationality,
	ranked_age.age AS second_highest_age
FROM ranked_age ranked_age
WHERE 1=1
	AND ranked_age.age_rank = 2
"""
fifth_result_df = pd.read_sql_query(fifth_query, con)
print(fifth_result_df)