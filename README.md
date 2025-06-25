# Random User Data Pipeline

### Objective

Create a python application that extracts at least 200 records from the RandomUser API, and then use an additional API to infer more information about the names obtained from the RandomUser API. Afte that, use SQL to perform 5 or more queries on the dataset that might yield interesting results.

### How to run

1. Project Setup
   Open Powershell (or any terminal) and create a project directory. Then, clone this GitHub repo to your machine:
   ```powershell
   cd Documents
   mkdir random_user_data_pipeline
   cd random_user_data_pipeline
   git clone https://github.com/Karns11/RandomUserDataPipeline.git
   cd RandomUserDataPipeline
   ```
2. Create/activate a python virtual environment
   I always prefer to work within venvs when using python so I will add this as a step here:

   ```powershell
    python -m venv .venv
    ./.venv/scripts/activate
   ```

   Make sure the (.venv) appears so you know the environment is active

3. Install the required libraries
   Make sure pip is updated:
   ```powershell
    python.exe -m pip install --upgrade pip
   ```
   Then, install the required dependencies for the application
   ```powershell
    Pip install requests pandas
   ```
4. Run the application
   The main python file is already provied in the repository: "users_data_loader.py"
   To run the application:
   ```powershell
    python users_data_loader.py
   ```
   NOTE: this application was designed to be run once per day in order to utilize the free tier of the enriching APIs. If you would like to run the application, but with a smaller output, you can pass an argument when running the application to determine how many member syou would like to be included in each group that is sent to the additional APIs.
   For example, you can run the following to command to run the program and include 50 users in each group. Since there are 3 additional APIs, the output will be 150 enriched users being saved to the database. This is a great feature to use when developing. The default is 100, which results in 300 enriched users being saved to the database to meet the 200 minimum requirement.
   ```powershell
    python users_data_loader.py 50
   ```
5. Expected Outcome
   Sqlite will create a users.db file in the project directory
   The enriched dataset will be stored in a Sqlite table named "users_names_data"
   Terminal output will confirm successful API calls and data storage
   API rate limits are respected in the logic, however if the application is run more than once per day, you will experience rate limiting.

Continue below for a detailed walkthrough of my solution and my thought process behind some of the decisions I made.

### Solution Summary

The application begins by imprting the required libraries, which in this case are: requests, pandas, sqlite3, and sys. I decided to use sqlite to store the data in preparation for the sql analysis portion of the assesment, since it is a very nice lighweight database solution that comes with python, and we are not working with a large dataset by any means. It also integrates really nice with DBeaver, which I already have installed on my machine. I also decided to use pandas for any data manipulation and cleaning that I will complete in this project, since I have a great deal of experience with pandas. The requests library obviously will be very helpful when making API calls to the different end points, and sys will be used to stop the application if I run into certian situations.

```python
# import required libraries
import requests
import pandas as pd
import sqlite3
import sys
```

Directly after importing the libraries, I set up my connection to the sqlite database and create the cursor, like so:

```python
# initialize sqlite connection to a new users database, and create cursor
con = sqlite3.connect('users.db')
cur = con.cursor()
```

Then, the application retrieves exactly 300 random users from the RandomUser API. To make the API calls, I will use python's request librarywhich makes the process super easy. Here, I will use the requsts.get() method to make the get request, I will then use the response to check the status code. if the status code is 200, then I will be good to go ahead and parse the data, and obtain the results. If the response is not a 200, then there is no need to continue on with the rest of the application. Therefore, I will print the status code, and exit the program.

```python
# make get request to random user api
random_user_response = requests.get(random_user_url, params = random_user_params)

if random_user_response.status_code == 200:
    json_data = random_user_response.json()
    json_results = json_data['results']

    print("Successfully obtained 300 random users\n")
else:
    print(f"Error. Random user api get request failed with a status code: {random_user_response.status_code}. Exiting application.\n")
    sys.exit(1)
```

Then, once the users list has been obtained, the next step is to flatten the JSON object that is returned into a list of user dictionaries. I also will only keep fields that I think will be relevant for analysis at the end. No need to keep any usernames, passwords, SSNs, etc. To do that, I used the following code:

```python
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
```

Next, now that I have one list containing 300 user dictionaries, before converting to a pandas dataframe, I will slice the list into 3 separate lists of 100. This will allow me to utilize the additional APIs that are required for this assesment. Since each of the additional APIs have a free tier that only allows you to make up to 100 calls a day, I will send the 100 first names from the first list to the agify API, the 100 first names from the second list to the genderize API, and the 100 last names from the third list to the nationalize API. This will make sure that every record has been enriched while making sure that I utilize as much of the free tiers for each additional API that I possibly can.

It would also be valid to use a completely different api with a more generous free tier, but I think it will be interesting to solve the problem this way, and showcase my ability to make multiple different API calls in order to enrich the dataset.

Here, you can see that I am looping through each user in each dataset, using an f string to pass the name as a paramter to the api endpoint, parsing the json if a successful response, adding 3 flags along with the target datapoint to the current user, and then finally appending that enriched user to a new list.

An interesting note is as follows: If I receive any non-200 response, then my application will print the status code received, and break out of the loop. If the non-200 response is a 429 response, that means the application reached the rate limit, and it should not make any additional calls. If there were any sucessful responses, then that data will have been appened to the respective list, and the program will carry on.

I think this is the best way to solve the not-so-generous free tier while still being able to utilize the 3 additional APIs to enrich the data.

```python

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
```

The next step my application takes is to union the 3 resulting lists together into one pandas data frame. You might've noticed above, that I added 3 additional fields in addition to the target datapoint for each individual list. That was in preparation for this step. I wanted to make sure 1) that every dataset has the same number of fields before unioning (even though the concat method handles that nicely) and 2) that these flags exists in order to make it easier to isolate the users that were within each group when completing downstream abalysis.

I faced the decision of keeping the 3 data frames separate and then loading each of them as their own table into the database, but I decided against that because 1) that really wouldn't make too much sense and 2) it is really simple to union different data frames together using pandas:

```python
# use pandas concat method to union all 3 dataframes togther in preparation of savings to table in sqlite database.
final_users_df = pd.concat([enriched_agify_users_df, enriched_genderize_users_df, enriched_nationalize_users_df], ignore_index=True)
```

Next, I made sure to create the table in the database in advance before saving the data frame to the table. I prefer doing this before hand because I prefer to have full control over the data types, rather than having pandas determine that when loading. So, here is my DDL for that:

```python
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

```

Lastly, I perform some slight data cleaning before saving the data to the table in the database. In the following code, I first check to make sure that the data frame exists and that there is data within it. If the data frame does not exist or is empty, that means there were issues with the additional APIs and the data should not be saved to the database unless it has been enriched with the additional APIs first.

If the data frame does exist and there is data within it, I make sure to convert the birth_date field to a date, rather than a datetime, using pandas, and then replace the data in the database with the new records. I figured this method would be acceptable for this use case since the main objective is to view python and sql analysis skills. However, a perfectly acceptable alternative would be to add a "processdate" field to the dataset here, and then append the data rather than replace it. that will allow the user of the data to isolate users that were loaded on a certain date, for example. In a production system, that might be a good idea.

```python
# slight data cleaning - store birthdate field as date and save dataframe to database
if final_users_df is not None and not final_users_df.empty:
    final_users_df['birth_date'] = pd.to_datetime(final_users_df['birth_date']).dt.date

    # always overwrite the raw DataFrame to a table called 'users_names_data'
    final_users_df.to_sql('users_names_data', con, if_exists='replace', index=False)

    print("Saved data frame successfully to db.")
else:
    print("Data frame is empty. Unable to save to db.")
```
