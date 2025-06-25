"""
Python application to obtain a list of random users from the randomuser api, enrich the data by passing the names into 1 of 3 apis in order to 
predict the age, gender, and nationality of the name, store the data in a sqlite databse in preparation for analytics via sql queries.

Libraries used:
    -requests
    -pandas
    -sqlite3 

-Import required libraries
-Set up sqlite database connection
-Make get request to random user api to get a list of 300 random users
    -If sucessful, parse the json data and create json object based on results
    -If unsuccessful, print response code and exit application. No data to continue with
-With successful response, flatten the json object anbd retain only relevant fields
-Split data set into 3 differnt groups of 100. (Due to rate limits with api's used for enriching, only 100 requests can be made per day)
-Group 1's first names sent to agify api in order to predict the age, then create agified flag, genderized_flag, and nationalized_flag to be used for unioning 
    the data together seamlessly
-Group 2's first names sent to genderize api in order to predict the gender, then create agified flag, genderized_flag, and nationalized_flag to be used for unioning 
    the data together seamlessly
-Group 3's last names sent to nationalize api in order to predict the nationality (retain only highest probability nationality from response), then create 
    agified flag, genderized_flag, and nationalized_flag to be used for unioning the data together seamlessly
-Union 3 groups of data together
-Create sql table in sqlite database 
-Perform slight data cleaning, and load data into sqlite table
"""

# import required libraries
import requests
import pandas as pd
import sqlite3
import sys

# initialize sqlite connection to a new users database, and create cursor
con = sqlite3.connect('users.db')
cur = con.cursor()

# define the random user api, add params to make sure exactly 300 records are returned
random_user_url = "https://randomuser.me/api/"
random_user_params = {'results': '300'}

# make get request to random user api
random_user_response = requests.get(random_user_url, params = random_user_params)

# If 200 response received, parse json data and obtain results. Else, log response and throw error
if random_user_response.status_code == 200:
    json_data = random_user_response.json()
    json_results = json_data['results']

    print("Successfully obtained 300 random users\n")
else:
    print(f"Error. Random user api get request failed with a status code: {random_user_response.status_code}. Exiting application.\n")
    sys.exit(1)


# flatten the json data while retaining only necessary fields
flattened_users_dataset = []
for user in json_results:
    flattened_user = {
        'first_name': user['name']['first'],
        'last_name': user['name']['last'],
        'title': user['name']['title'],
        'gender': user['gender'],
        'email': user['email'],
        'phone': user['phone'],
        'cell': user['cell'],
        'nationality': user['nat'],
        'birth_date': user['dob']['date'],
        'age': user['dob']['age'],
        'address': f"{user['location']['street']['number']} {user['location']['street']['name']}",
        'city': user['location']['city'],
        'state': user['location']['state'],
        'country': user['location']['country'],
        'postcode': user['location']['postcode'],
        'latitude': user['location']['coordinates']['latitude'],
        'longitude': user['location']['coordinates']['longitude']
    }
    
    flattened_users_dataset.append(flattened_user)


# split flattened data set into 3 groups of 100 to be used with additional apis
users_dataset_send_to_agify = flattened_users_dataset[:100]
users_dataset_send_to_genderize = flattened_users_dataset[100:200]
users_dataset_send_to_nationalize = flattened_users_dataset[200:300]


# send first group of 100 names to agify api, then create flags to be used for seamless unioning later on
enriched_agify_dataset = []
for user in users_dataset_send_to_agify:
    agify_url = f"https://api.agify.io?name={user['first_name']}"
    agify_response = requests.get(agify_url)

    agify_reset_timer = agify_response.headers.get("X-Rate-Limit-Reset")

    if agify_response.status_code == 200:
        agify_json_data = agify_response.json()
    
        user['agify_predicted_age'] = agify_json_data['age']
        user['agified_flag'] = 1
        user['genderized_flag'] = 0
        user['nationalized_flag'] = 0

        enriched_agify_dataset.append(user)
    else:
        print(f"Error. Agify get request failed with a status code: {agify_response.status_code}.")
        if agify_response.status_code == 429:
            print(f"You've been rate limited. You can try again in {agify_reset_timer} seconds\n")
            break

#convert agify dataset to pandas dataframe
enriched_agify_users_df = pd.DataFrame(enriched_agify_dataset)


# send second group of 100 names to genderize api, then create flags to be used for seamless unioning later on
enriched_genderize_dataset = []
for user in users_dataset_send_to_genderize:
    genderize_url = f"https://api.genderize.io?name={user['first_name']}"
    genderize_response = requests.get(genderize_url)

    genderize_reset_timer = genderize_response.headers.get("X-Rate-Limit-Reset")

    if genderize_response.status_code == 200:
        genderize_json_data = genderize_response.json()
    
        user['genderize_predicted_gender'] = genderize_json_data['gender']
        user['agified_flag'] = 0
        user['genderized_flag'] = 1
        user['nationalized_flag'] = 0
    
        enriched_genderize_dataset.append(user)
    else:
        print(f"Error. Genderize get request failed with a status code: {genderize_response.status_code}.")
        if genderize_response.status_code == 429:
            print(f"You've been rate limited. You can try again in {genderize_reset_timer} seconds\n")
            break

#convert genderize dataset to pandas dataframe
enriched_genderize_users_df = pd.DataFrame(enriched_genderize_dataset)


# send third group of 100 names to nationalize api, then create flags to be used for seamless unioning later on
enriched_nationalize_dataset = []
for user in users_dataset_send_to_nationalize:
    nationalize_url = f"https://api.nationalize.io/?name={user['last_name']}"
    nationalize_response = requests.get(nationalize_url)

    nationalize_reset_timer = nationalize_response.headers.get("X-Rate-Limit-Reset")

    if nationalize_response.status_code == 200:
        nationalize_json_data = nationalize_response.json()
    
        country_highest_prob = None
        highest_prob = 0
        
        for country in nationalize_json_data['country']:
            if country['probability'] > highest_prob:
                highest_prob = country['probability']
                country_highest_prob = country['country_id']
    
        user['nationalize_predicted_country'] = country_highest_prob
        user['agified_flag'] = 0
        user['genderized_flag'] = 0
        user['nationalized_flag'] = 1    
        enriched_nationalize_dataset.append(user)
    else:
        print(f"Error. Nationalize get request failed with a status code: {nationalize_response.status_code}.")
        if nationalize_response.status_code == 429:
            print(f"You've been rate limited. You can try again in {nationalize_reset_timer} seconds\n")
            break

#convert nationalize dataset to pandas dataframe
enriched_nationalize_users_df = pd.DataFrame(enriched_nationalize_dataset)


# use pandas concat function to union all 3 dataframes togther in preparation of savings to table in sqlite database.
final_users_df = pd.concat([enriched_agify_users_df, enriched_genderize_users_df, enriched_nationalize_users_df], ignore_index=True)


# Create table in sqlite database if it doesn't already exist
cur.execute("""
CREATE TABLE IF NOT EXISTS users_names_data (
    first_name TEXT,
    last_name TEXT,
    title TEXT,
    gender TEXT,
    email TEXT,
    phone TEXT,
    cell TEXT,
    nationality TEXT,
    birth_date TEXT, 
    age INTEGER,
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    postcode TEXT,
    latitude TEXT,
    longitude TEXT,
    agify_predicted_age INTEGER,
    genderize_predicted_gender TEXT,
    nationalize_predicted_country TEXT,
    agified_flag INTEGER,
    genderized_flag INTEGER,
    nationalized_flag INTEGER
)
""")
con.commit()


# slight data cleaning - store birthdate field as date and save dataframe to database
if final_users_df is not None and not final_users_df.empty:
    final_users_df['birth_date'] = pd.to_datetime(final_users_df['birth_date']).dt.date

    # always overwrite the raw DataFrame to a table called 'users_names_data'
    final_users_df.to_sql('users_names_data', con, if_exists='replace', index=False)

    print("Saved data frame successfully to db.")
else:
    print("Data frame is empty. Unable to save to db.")