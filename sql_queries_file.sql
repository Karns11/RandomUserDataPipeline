--Some queries were created with some inspiration from DataLemur. I have spent tons of time on that website practicing SQL skills, and wanted to replicate some of those questions here.
--Most queries were created with the intention of using a cte or window function, bui not all.

-- 1. Return users (all fields) who have an actual age that is above the average for the users actual country fpr the entire dataset.
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
	AND (age > avg_age);

	
	

-- 2. Return a histogram of distinct first names per state. AKA group the states by number of distinct names
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




-- 3. Return number of correct predictions, incorrect predictions, and prediction accuracy % order by highest prediction accuracy %.
SELECT
    country,
    COUNT(*) AS total_records,
    SUM(CASE WHEN LOWER(gender) = LOWER(predicted_gender) THEN 1 ELSE 0 END) AS correct_predictions,
    SUM(CASE WHEN LOWER(gender) != LOWER(predicted_gender) THEN 1 ELSE 0 END) AS incorrect_predictions,
    ROUND((SUM(CASE WHEN LOWER(gender) = LOWER(predicted_gender) THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 2) AS prediction_accuracy_percent
FROM users_names_data
WHERE 1=1
	AND predicted_gender IS NOT NULL
	AND gender IS NOT NULL
GROUP BY country
ORDER BY prediction_accuracy_percent DESC;



-- 4. Write a query to determine the most common birth month by country. Using at least 1 cte to answer this question.
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
WHERE rank_num = 1;



-- 5. Write a query to return the 2rd highest age (maybe could do predicted age with a full dataset) by nationality
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

	
