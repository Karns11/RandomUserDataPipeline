--These sql queries, through the use of best practices, display my ability to construct complex queries in order to solve unique business problems. 
--Each query was designed based on real-world scenarios I've encountered, with the goal of producing meaningful insights.

--Some best practices used here:
	--Prioritizing readability through consistent use of aliases.
		--Every table is aliased with a descriptive name, and every query includes qualified column referencing. I know, from experience, that this is key when creating queries.
	--Consistent Formatting.
		--Every SQL keyword is in uppercase while every non-keyword is in lowercase. This is consistent throughout each query.
	--Prioritizes inner joins over outer joins. 
		--This is an optimization technique that I have learned over time. 
		--If you expect the data to be there in a join, always use an inner join to reduce the number of records being returned.
	--Use of CTEs for breaking down problems into smaller steps, logically



-- 1. Above-Average Age by Country.
--Why this is interesting: This query highlights users that are outliers in terms of their age compared to the average age for their country.
--This type of analysis is a common one when it comes to demographic analyses, and I have applied similar logic in real-world projects.
WITH country_avg_age AS (
	SELECT 
		users_data.country,
		ROUND(AVG(users_data.age), 2) AS avg_age
	FROM users_names_data users_data
	GROUP BY users_data.country
),

add_avg_age AS (
	SELECT 
		users_data.first_name,
		users_data.last_name,
		users_data.gender,
		users_data.country,
		users_data.age,
		avg_age_cte.avg_age
	FROM users_names_data users_data
	JOIN country_avg_age avg_age_cte -- more efficient than left join bc we only want records that match
		ON users_data.country = avg_age_cte.country
)

SELECT 
	add_avg_age_cte.first_name,
	add_avg_age_cte.last_name,
	add_avg_age_cte.gender,
	add_avg_age_cte.country,
	add_avg_age_cte.age,
	add_avg_age_cte.avg_age,
	abs(add_avg_age_cte.age - add_avg_age_cte.avg_age) AS difference
FROM add_avg_age add_avg_age_cte
WHERE 1=1
	AND (add_avg_age_cte.age > add_avg_age_cte.avg_age)
ORDER BY difference;
	
	

-- 2. First name diversity by state. AKA a histogram of distinct first names per state.
--Why this is interesting: Allows me to see naming diversity across states. These types of queries can be used to support marketing segmentation efforts, for example. 
--I obtained inspiration to create this query from Data Lemur. I have spent tons of time on that website solving queries and I wanted to recreate one of those queries in this context.
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
ORDER BY num_distinct_first_names.num_dist_first_names;




-- 3. Predicted VS Actual Gender Comparison.
--Why this is interesting: This query examines the result of the namsor api. I wanted to make sure I include a query that displays an analysis of the namsor api.
--Here we can see the # of correct and incorrect predictions, along with the prediction accuracy broken out my country
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



-- 4. Most Common Birth Month by Country.
--Why this is interesting: Identify patterns in birth month by country. This uses a window function to solve the problem and I provide a couple of different options depending on DMS in use.
--This is another type of query that I have lots experience with in real-world projects. A common use case for a query like this is marketing campaigns.
WITH num_birth_months_per_country AS (
	SELECT
		users_data.first_name,
		users_data.last_name,
		users_data.birth_date,
		users_data.country,
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
WHERE rank_num = 1
ORDER BY add_rank_cte.num;



-- 5. Second highest age by nationality.
--Why this is interesting: This type of query demonstrates my advanced SQL knowledge when it comes to ranking logic and window functions. 
--I have created several similar "runner-up" queries in real-world scenarios, especially when it comes to determining second place results for marketing campaigns.
WITH ranked_age AS (
	SELECT 
		users_data.first_name,
		users_data.last_name,
		users_data.birth_date,
		users_data.country,
		users_data.nationality,
		users_data.age,
		RANK() OVER (PARTITION BY users_data.nationality ORDER BY users_data.age DESC) AS age_rank
	FROM users_names_data users_data
)

SELECT
	DISTINCT
	ranked_age_cte.nationality,
	ranked_age_cte.age AS second_highest_age
FROM ranked_age ranked_age_cte
WHERE 1=1
	AND ranked_age_cte.age_rank = 2
ORDER BY ranked_age_cte.age  DESC;
	
