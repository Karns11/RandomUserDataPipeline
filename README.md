# Random User Data Pipeline

## Table of Contents

- [Objective](#objective)
  -This contains information on how to run the sql queries after the main application has be run successfully. The two options are 1) running the sql queries that exist in the 'sql_queries_file.sql' sql file in a database management tool like dbeaver (steps to install dbeaver and connect to the database are below) 2) running the python file in this directory named 'five_sql_queries_python_script.py'. This file contains the exact same queries, but runs them using sqlite3 and pandas. All results are returned as a pandas data frame.
- [How to Run the Application](#how-to-run-the-application)
  -This contains information on how to run the application to populate the end database with the random user data.
- [How to Run SQL Queries](#how-to-run-sql-queries)
  -This contains information on how to run the sql queries after the main application has be run successfully. The two options are 1) running the sql queries that exist in the 'sql_queries_file.sql' sql file in a database management tool like dbeaver (steps to install dbeaver and connect to the database are below) 2) running the python file in this directory named 'five_sql_queries_python_script.py'. This file contains the exact same queries, but runs them using sqlite3 and pandas. All results are returned as a pandas data frame.
- [Solution Summary](#solution-summary)
  -This sections contains a detailed walkthrough of the code I wrote to fetch data from the random users api, use an additional api to enrich the data, and save the data set to a sqlite database.

### Objective

Create a Python application that extracts at least 200 records from the RandomUser API, and then use an additional API to infer more information about the names obtained from the RandomUser API. After that, use SQL to perform 5 or more queries on the dataset that might yield interesting results.

I hope you enjoy this solution, and I appreciate the opportunity to work on this!

### How to run the application

NOTE: You must obtain a free api key from the namsor api. The steps on how to obtain that api key are under number 4 below.

1. Project Setup
   Open Powershell (or any terminal) and create a project directory. Then, clone this GitHub repo to your machine:
   ```powershell
   cd Documents
   mkdir random_user_data_pipeline
   cd random_user_data_pipeline
   git clone https://github.com/Karns11/RandomUserDataPipeline.git
   cd RandomUserDataPipeline
   ```
2. Create/activate a Python virtual environment
   I always prefer to work within venvs when using Python so I will add this as a step here:

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
    pip install requests pandas python-dotenv
   ```

4. Obtain a free api key from namsor:

   Navigate to https://namsor.app/. From there, create free account. Then, you will have to verify your email address. After that, you can then copy api key from the dashboard section here: https://namsor.app/my-account/.

5. Create .env file to store the api key, rather than hard-coding it in the application itself.
   Within the .env file, you should create a NAMSOR_API_KEY variable.

   The easiest way to do that is to run the following command to open vscode and then create the .env file in the project directory.

   ```
   code .
   ```

   If you don't have vscode installed, any text editor will do, just make sure the .env file is in the project directory, and then enter the following:

   ```
    NAMSOR_API_KEY=<your api key>
   ```

6. Run the application
   The main Python file is already provided in the repository: "users_data_loader.py"
   To run the application:
   ```powershell
    python users_data_loader.py
   ```
   NOTE: You can customize the application by adding an additional parameter to determine how many users to grab from the random user api. Default is 300. Max per run is 300.
   ```powershell
    python users_data_loader.py 50
   ```
7. Expected Application Outcome

   SQLite will create a users.db file in the project directory

   The enriched dataset will be stored in a SQLite table named "users_names_data"

   Terminal output will confirm successful API calls and data storage

   Should take less than a minute to run, depending on how many users are returned

   Successful run will look something like:

   ```
    Making api call to random users api...

    Successfully obtained 200 random users

    Making api calls to namsor api...

    Total rows in final users df: 200

    Saved data frame successfully to db.
   ```

   NOTE: when running the pipeline for 200 or more users, expect the process to finish successfully after about 2 minutes.

### How to run sql queries

There are a couple of different options when it comes to running the 5 SQL queries on top of the resulting dataset.

The first option is to run the 'five_sql_queries_python_script.py' file that exists in the same project directory. This will run all of the SQL queries I created that I thought yielded interesting results. This script will output everything in an easy-to-read format in the terminal. You can run this command:

```
python five_sql_queries_python_script.py
```

Additionally, if you would like to run the queries in a database management tool, like dbeaver, I included the .sql file that contains the queries as well. These can be run directly within the tool which provides a more familiar workspace. Here are the steps to install dbeaver and hook it up to the database, if needed:

1. Navigate to https://dbeaver.io/download/ and download the community edition for your machine
2. Launch the application and install everything it prompts for and create a desktop shortcut
3. Once the application is open, click on the ‘New Database Connection’ button from the top menu. In the list of databases, select SQLite, then click next
4. Browse your device to find the users.db file that was created after running the application to load the data
5. Test the connection. If drivers are missing, it will prompt you to install them. Once successful, click finish

Below are my results for each of the 5 queries. (More detail can be found in the sql query files).

1. Query 1. Above-Average Age by Country.

![Query 1](https://github.com/Karns11/RandomUserDataPipeline/blob/main/SQL%20Results%20Images/Query1.png)

2. Query 2. First name diversity by state. AKA a histogram of distinct first names per state.

![Query 2](https://github.com/Karns11/RandomUserDataPipeline/blob/main/SQL%20Results%20Images/Query2.png)

3. Query 3. Predicted VS Actual Gender Comparison.

![Query 3](https://github.com/Karns11/RandomUserDataPipeline/blob/main/SQL%20Results%20Images/Query3.png)

4. Query 4. Most Common Birth Month by Country.

![Query 4](https://github.com/Karns11/RandomUserDataPipeline/blob/main/SQL%20Results%20Images/Query4.png)

5. Query 5. Second highest age by nationality.

![Query 5](https://github.com/Karns11/RandomUserDataPipeline/blob/main/SQL%20Results%20Images/Query5.png)

Now, you can open either of the sql files file and run the queries within them! The sql files contain more information about why I chose to create each query, why the results are interesting, and common real-world scenarios where I created similar queries. All of the queries and information is the same within each file. Just two different options for executing the queries.

Continue below for a detailed walkthrough of my python solution and my thought process behind some of the decisions I made.

### Solution Summary

Here, I would like to walk through my entire solution and provide some explanations about some of the decisions I made.

The application begins by importing the required libraries, which in this case are: requests, pandas, SQLite3, sys, time, os, and dotenv. I ultimately decided to use SQLite to store the data in preparation for the sql analysis portion of the assessment. Since it is a very nice lightweight database solution that comes with Python, and we are not working with a large dataset by any means, I figured this would be the perfect solution. It also integrates really nicely with DBeaver, which I already have installed on my machine. If this were intended for production or larger data pipelines, a more robust RDBMS like Postgres would be preferable.

I also decided to use pandas for any data manipulation and cleaning that I will complete in this project, since I have a great deal of experience with pandas. The requests library obviously will be very helpful when making API calls to the different end points. The sys library will be used to stop the application if I run into certain situations. The time library can potentially be used to create delays when looping through datasets and making calls to the namsor api. The os and dotenv libraries will be used to obtain the api key from the .env file so I don't have to hard code the value in the application. An API key is needed when interacting with the namsor API.

Also, I added the functionality to pass an optional parameter when running the application, so below where the libraries are being imported, I created the logic to assign the argument to a variable to be used with limiting the number of responses from the random user api. Incorporating this functionality lets me quickly test smaller samples during development or debugging, instead of always retrieving a full dataset. This, in my opinion, is a best-practice that I always try to use.

The last part of this first section includes the logic to load in the env variables. This is best-practice when working with API keys, so I have a great deal of experience with doing so.

```python
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
```

Directly after importing the libraries, assigning the parameter to a variable, and loading in the api key env variable, I set up my connection to the SQLite database and created the cursor, like so:

```python
# initialize SQLite connection to a new users database, and create cursor to interact with the database later on
con = sqlite3.connect('users.db')
cur = con.cursor()
```

Then, the application retrieves, by default, exactly 300 random users from the RandomUser API. To make the API calls, I will use Python's request library which makes the process very straightforward. Here, I will use the requests.get() method to make the get request, I will then use the response to check the status code. if the status code is 200, then I will be good to go ahead and parse the data, and obtain the results. If the response status code is not 200, there is no need to continue running the application. I will print the status code and exit.

```python
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

Next, I will pass each of the names in the resulting dataset to the namsor api. Namsor has an api endpoint to genderize a given first and last name. So, I will loop through each of the users, pass the first and last name as parameters to genderize the names, and then retain a handful of interesting returned fields to be used for analysis later on. I made the decision to not use the following APIs: https://nationalize.io/, https://genderize.io/, https://agify.io/, since they have very strict rate limits (only 100 per day for all). As a result, I came across the Namsor api which is very similar but has a more generous free tier (as long as you create a free account and include the api key as a header in the request).

So, here is how I handled that logic:

```python
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
```

Sending an API key as a header with each request is a type of authentication that I am super familiar with. I have used a ton of APIs that require this type of authentication, so it was really simple to include that logic.

Next, I made sure to create the table in the database in advance before saving the data frame to the table. I prefer doing this beforehand because I prefer to have full control over the data types, rather than having pandas determine that when loading. So, here is my DDL for that:

```python
# Create table in SQLite database if it doesn't already exist
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

```

Lastly, I perform some slight data cleaning before saving the data to the table in the database. In the following code, I first check to make sure that the data frame exists and that there is data within it. If the data frame does not exist or is empty, that means there were issues with the additional APIs and the data should not be saved to the database unless it has been enriched with the additional APIs first.

If the data frame does exist and there is data within it, I make sure to convert the birth_date field to a date, rather than a datetime, using pandas, and then replace the data in the database with the new records. I figured this method would be acceptable for this use case since the main objective is to demonstrate Python and SQL analysis skills.

```python
# slight data cleaning - store birthdate field as date and save dataframe to database
if enriched_namsor_users_df is not None and not enriched_namsor_users_df.empty:
    enriched_namsor_users_df['birth_date'] = pd.to_datetime(enriched_namsor_users_df['birth_date']).dt.date

    # always overwrite the raw DataFrame to a table called 'users_names_data'
    enriched_namsor_users_df.to_sql('users_names_data', con, if_exists='replace', index=False)

    print("Saved data frame successfully to db.")
else:
    print("Data frame is empty. Unable to save to db.")
```
