"""
Python script that allows the user to run the sql queries and view the results in a pandas dataframe if that is preferred over a database management system like dbeaver

These sql queries, through the use of best practices, display my ability to construct complex queries in order to solve unique business problems. 
Each query was designed based on real-world scenarios I've encountered, with the goal of producing meaningingful insights.

Some best practices used here:
	-Prioritizing readability through consistent use of aliases.
		-Every table is aliased with a descriptive name, and every query includes qualified column referencing. I know, from experience, that this is key when creating queries.
	-Consistent Formatting.
		-Every SQL keyword is in uppercase while every non-keyword is in lowercase. This is consistent throughout each query.
	-Prioritizes inner joins over outer joins. 
		-This is an optimization technique that I have learned over time. 
		-If you expect the data to be there in a join, always use an inner join to reduce the number of records being returned.
	-Use of CTEs for breaking down problems into smaller steps, logically
"""

import sqlite3
import pandas as pd

# Connect to the SQLite database
con = sqlite3.connect('users.db')
cur = con.cursor()

# 1. Above-Average Age by Country,
# Why this is interesting: This query highlights users that are outliers in terms of their age compared to the average age for their country.
# This type of analysis is a common one when it comes to demographic analyses, and I have applied similar logic in real-world projects.
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
FROM add_avg_age avg_age
WHERE 1=1
	AND (avg_age.age > avg_age.avg_age);
"""
first_result_df = pd.read_sql_query(first_query, con)
print(first_result_df)



# 2. First name diversity by state. AKA a histogram of distinct first names per state.
# Why this is interesting: Allows me to see naming diversity across states. These types of queries can be used to support marketing segmentation efforts, for example. 
# I obtained inspiration to create this query from Data Lemur. I have spent tons of time on that website solving queries and I wanted to recreate one of those queries in this context.
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
GROUP BY num_distinct_first_names.num_dist_first_names;
"""
second_result_df = pd.read_sql_query(second_query, con)
print(second_result_df)



# 3. Predicted VS Actual Gender Comparison
# Why this is interesting: This query examines the result of the namsor api. I wanted to make sure I include a query that displays an analysis of the namsor api.
# Here we can see the # of correct and incorrect predictions, along with the prediction accuracy broken out my country
print("\n3. Return number of correct predictions, incorrect predictions, and prediction accuracy % order by highest prediction accuracy %. \n")
third_query = f"""
SELECT
    users_data.country,
    COUNT(*) AS total_records,
    SUM(CASE WHEN LOWER(users_data.gender) = LOWER(users_data.predicted_gender) THEN 1 ELSE 0 END) AS correct_predictions,
    SUM(CASE WHEN LOWER(users_data.gender) != LOWER(users_data.predicted_gender) THEN 1 ELSE 0 END) AS incorrect_predictions,
    ROUND((SUM(CASE WHEN LOWER(users_data.gender) = LOWER(users_data.predicted_gender) THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 2) AS prediction_accuracy_percent
FROM users_names_data users_data
WHERE 1=1
	AND users_data.predicted_gender IS NOT NULL
	AND users_data.gender IS NOT NULL
GROUP BY users_data.country
ORDER BY prediction_accuracy_percent DESC;
"""
third_result_df = pd.read_sql_query(third_query, con)
print(third_result_df)




# 4. Most Common Birth Month by Country
# Why this is interesting: Identify patterns in birth month by country. This uses a window function to solve the problem and I provide a couple of different options depending on DMS in use.
# This is another type of query that I have lots experience with in real-world projects. A common use case for a query like this is marketing campaigns.
print("\n4. Write a query to determine the most common birth month by country. Using at least 1 cte to answer this question. \n")
fourth_query = f"""
WITH num_birth_months_per_country AS (
	SELECT
		*,
--		COUNT(*) OVER (PARTITION BY users_data.country, MONTH(users_data.birth_date)) AS num --Not allowed in sqlite. Is allowed in sqlserver.
		COUNT(*) OVER (PARTITION BY users_data.country, strftime('%m', users_data.birth_date)) AS num 
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
WHERE rank_num = 1;
"""
fourth_result_df = pd.read_sql_query(fourth_query, con)
print(fourth_result_df)


# 5. Second highest age by nationality
# Why this is interesting: This type of query demonstrates my advanced SQL knowledge when it comes to ranking logic and window functions. 
# I have created several similar "runner-up" queries in real-world scenarios, especially when it comes to determining second place results for marketing campaigns.
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
	AND ranked_age.age_rank = 2;
"""
fifth_result_df = pd.read_sql_query(fifth_query, con)
print(fifth_result_df)