# Random User Data Pipeline

### Objective

Create a python application that extracts at least 200 records from the RandomUser API, and then use an additional API to infer more information about the names obtained from the RandomUser API. Afte that, use SQL to perform 5 or more queries on the dataset that might yield interesting results.

### Solution Summary

The application begins by retrieving exactly 300 random users from the RandomUser API. To make the API calls, I will use python's request librarywhich makes the process super easy. Here, I will use the requsts.get() method to make the get request, I will then use the response to check the status code. if the status code is 200, then I will be good to go ahead and parse the data, and obtain the results. If the response is not a 200, then there is no need to continue on with the rest of the application. Therefore, I will print the status code, and exit the program.

```python
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

Next, now that I have one list containing 300 user dictionaries, before converting to a pandas dataframe, I will slice the list into 3 separate lists of 100. This will allow me to utilize the additional APIs that are required for this assesment. Since each of the additional APIs have a free tier that only allows you to make up to 100 calls a day, I will send the 100 first names from the first list to the agify API, the 100 first names from the second list to the genderize API, and the 100 last names from the third list to the nationalize API.

This will make sure that every record has been enriched while maintaining under the threshold for the free tier for each additional API. It would also be valid to use a completely different api with a more generous free tier, but I think it will be interesting to solve the problem this way, and showcase my ability to make multiple different API calls in order to enrich the dataset. So, here is my code for what I just described:

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
