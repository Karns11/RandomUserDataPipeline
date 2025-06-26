"""
Python application to obtain a list of random users from the randomuser api, enrich the data by passing the names into 1 of 3 apis in order to 
predict the age, gender, and nationality of the name, store the data in a sqlite databse in preparation for analytics via sql queries.

Libraries used:
    -requests
    -pandas
    -sqlite3 
    -sys
    -time

-Import required libraries
-Set up sqlite database connection
-Make get request to random user api to get a list of 300 random users
    -If sucessful, parse the json data and create json object based on results
    -If unsuccessful, print response code and exit application. No data to continue with
-With successful response, flatten the json object anbd retain only relevant fields
-Send first and last name to namsor api to getredicted gender. Use this to compare to actual gender in SQL queries later on.
-Create sql table in sqlite database 
-Perform slight data cleaning, and load data into sqlite table
"""

# import required libraries
import requests
import pandas as pd
import sqlite3
import sys
import time
import os
from dotenv import load_dotenv

# Get parameter from command line, default to 300 and it cannot be more than 300. Determines how many users to get data for.
if len(sys.argv) > 1:
    int_argument = int(sys.argv[1])
    if int_argument > 300:
        num_users = 300
    else:
        num_users = int_argument
else:
    num_users = 300

# Load in api key from .env file. If no api key, exit application with log message
load_dotenv()
API_KEY = os.getenv("NAMSOR_API_KEY")
if not API_KEY:
    print("Error: api key not found in environment variables. Exiting application.")
    sys.exit(1)

# initialize SQLite connection to a new users database, and create cursor to interact with the database later on
con = sqlite3.connect('users.db')
cur = con.cursor()

# define the random user api, add params to make sure exactly 300 records are returned
random_user_url = "https://randomuser.me/api/"
random_user_params = {'results': num_users}

# make get request to random user api
print("Making api call to random users api...\n")
random_user_response = requests.get(random_user_url, params = random_user_params)

# If 200 response received, parse json data and obtain results. Else, log response and throw error
if random_user_response.status_code == 200:
    json_data = random_user_response.json()
    json_results = json_data['results']

    print(f"Successfully obtained {num_users} random users\n")
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


# send all names to namsor api, then extract predicted gender
print("Making api calls to namsor api...\n")
enriched_namsor_dataset = []
for user in flattened_users_dataset:
    namsor_url = f"https://v2.namsor.com/NamSorAPIv2/api2/json/gender/{user['first_name']}/{user['last_name']}"
    namsor_headers = {
        "X-API-KEY": API_KEY
    }
    namsor_response = requests.get(namsor_url, headers=namsor_headers)

    if namsor_response.status_code == 200:
        namsor_json_data = namsor_response.json()
    
        user['predicted_gender'] = namsor_json_data['likelyGender']
        user['predicted_gender_score'] = namsor_json_data['score']
        user['predicted_gender_probabilityCalibrated'] = namsor_json_data['probabilityCalibrated']
    
        enriched_namsor_dataset.append(user)
    else:
        print(f"Error. Genderize get request failed with a status code: {namsor_response.status_code}.")
        if namsor_response.status_code == 429:
            print(f"You've been rate limited.\n")
            break

#convert genderize dataset to pandas dataframe
enriched_namsor_users_df = pd.DataFrame(enriched_namsor_dataset)

print(f"Total rows in final users df: {len(enriched_namsor_users_df)}\n")

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
    predicted_gender TEXT,
    predicted_gender_score NUMERIC,
    predicted_gender_probabilityCalibrated NUMERIC       
)
""")
con.commit()


# slight data cleaning - store birthdate field as date and save dataframe to database
if enriched_namsor_users_df is not None and not enriched_namsor_users_df.empty:
    enriched_namsor_users_df['birth_date'] = pd.to_datetime(enriched_namsor_users_df['birth_date']).dt.date

    # always overwrite the raw DataFrame to a table called 'users_names_data'
    enriched_namsor_users_df.to_sql('users_names_data', con, if_exists='replace', index=False)

    print("Saved data frame successfully to db.")
else:
    print("Data frame is empty. Unable to save to db.")