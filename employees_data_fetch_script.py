import math
import shlex
import time
import requests
import traceback
# from EmailWhiz.emailwhiz_api.views import fetch_employees_data_from_apollo
from pymongo import MongoClient
from datetime import datetime


def replace_value_by_key(json_string, key, new_value):
  """Replaces the value of a specific key in a JSON-like string.

  Args:
    json_string: The JSON-like string.
    key: The key to replace.
    new_value: The new value to replace with.

  Returns:
    The modified JSON-like string.
  """

  # Find the start index of the key-value pair
  start_index = json_string.index(f'"{key}":')

  # Determine the end index based on the value type
  if isinstance(new_value, str):
    end_index = json_string.find('"', start_index + len(f'"{key}":') + 1)
    new_value_str = f'"{new_value}"'
  elif isinstance(new_value, list):
    new_value_str = ''
    for i in range(len(new_value)):
        new_value_str += '"' + new_value[i] + '"'
        if i != len(new_value) - 1:
            new_value_str += ','
    new_value_str = f'[{new_value_str}]' 
    end_index = json_string.find(']', start_index + len(f'"{key}":') + 1)
  elif isinstance(new_value, int):
    end_index = json_string.find(',', start_index + len(f'"{key}":') + 1) -1 
    new_value_str = str(new_value)
  else:
    raise ValueError("Unsupported value type")

  # Replace the old value with the new one
  return json_string[:start_index + len(f'"{key}":')] + new_value_str + json_string[end_index+1:]


def parse_curl_command(curl_command):
    """
    Parse a curl command and return the equivalent Python request components.
    Supports extracting the URL, headers, and data.
    """
    tokens = shlex.split(curl_command)
    url = None
    headers = {}
    data = None

    # Iterate through tokens to extract information
    for i, token in enumerate(tokens):
        if token == "curl":
            continue
        elif token.startswith("http"):
            url = token
        elif token == "-H":
            header = tokens[i + 1].split(": ", 1)
            if len(header) == 2:
                headers[header[0]] = header[1]
        elif token in ("--data-raw", "-d"):
            data = tokens[i + 1]

    return url, headers, data


def fetch_employees_data_from_apollo(_data):

    organization_id, person_titles, person_locations = _data['organization_id'],  _data['person_titles'],  _data['person_locations']
    

    curl_request = _data['curl_request']
    # print("curl_request: ", curl_request)

    if not curl_request:
        return {'error': f"No CURL request found for Employees API"}

    try:
        # Parse the curl command
        url, headers, data = parse_curl_command(curl_request)
        
        if not url:
            return {'error': "Invalid CURL request: URL missing"}

        current_page = 1
        max_page = 1
        pages_found = False
        employees_addition_count = 0
        
        while current_page <= max_page:
            # Update the data payload

            # print(f"organization_id: {type(organization_id)} {organization_id} organization_id: {type(organization_id)} person_titles: {type(person_titles)} person_locations: {type(person_locations)} current_page: {type(current_page)}")
            data = replace_value_by_key(data, 'organization_ids', organization_id)
            data = replace_value_by_key(data, 'person_titles', person_titles)
            data = replace_value_by_key(data, 'person_locations', person_locations)
            data = replace_value_by_key(data, 'page', current_page)

            
            print("R2: Request Sent: ", data)
            # Perform the HTTP request
            response = requests.post(url, headers=headers, data=str(data))
            # print("R2: ", response.__dict__)
            if response.status_code == 401: 
                return {"error": response.__dict__["_content"].decode('utf-8')}
            print("R2 Response Code: ", response.status_code)
            response_data = response.json()
            # print("R2.1: ", response_data)
            if response.status_code != 200: 
                return response_data
            people = response_data.get('people', [])
            if pages_found == False:
                total_entries = response_data['pagination']['total_entries']
                if total_entries > 75:
                    max_page = 3
                else:
                    max_page = math.ceil(total_entries/25)
            print(f"max_page: {max_page}")
            if max_page == 0:
                print("Sleep Started..")
                time.sleep(60)
                print("Sleep Ended..")
                break
            if not people:
                break

            
            for person in people:
                employee_id = person.get('id')
                first_name = person.get('first_name')
                last_name = person.get('last_name')
                titles = person.get('title')
                city = person.get('city')
                country = person.get('country')
                email_status = person.get('email_status')
                is_likely_to_engage = person.get('is_likely_to_engage', False)
                # Insert or update employee data in apollo_emails
                result = apollo_emails_collection.update_one(
                    {'id': employee_id},
                    {
                        '$set': {
                            'first_name': first_name,
                            'last_name': last_name,
                            'city': city,
                            'country': country,
                            'timestamp': datetime.now(),
                            'organization_id': organization_id[0],
                            "email_status": email_status,
                            "is_likely_to_engage": is_likely_to_engage
                        },
                        '$addToSet': {
                            'titles': titles
                        },
                        '$setOnInsert': {
                            'email': ""  # Keep email empty
                        }
                    },
                    upsert=True
                )
                if result.modified_count == 0:
                    employees_addition_count += 1

            current_page += 1
            print("Sleep Started..", datetime.now())
            time.sleep(60)
            print("Sleep Ended..", datetime.now())


        # Mark organization as processed
        companies_collection.update_one(
            {'id': organization_id[0]},
            {'$set': {'is_processed': True}}
        )

        return {"success": True, "data": {'count': employees_addition_count}}

    except Exception as e:
        traceback.print_exc()
        return {'error': str(e)}

client = MongoClient('mongodb+srv://shoaibthakur23:Shoaib%40345@cluster0.xjugu.mongodb.net/')  # Replace with your MongoDB connection URI
db = client['EmailWhiz']  # Replace with your database name
companies_collection = db['companies'] 
and_collection = db['and_company_keywords']
subject_collection = db['subjects']
combination_collection = db['combinations_company_keywords']
apollo_apis_curl_collection = db['apollo_apis_curl']
apollo_emails_collection = db['apollo_emails']
apollo_emails_sent_history_collection = db['apollo_emails_sent_history']


# # URL to send the request to
# url = "http://0.0.0.0:8000/api/fetch-employees/"

# # Headers for the request
# headers = {
#     "Accept": "*/*",
#     "Accept-Language": "en-US,en",
#     "Connection": "keep-alive",
#     "Content-Type": "application/json",
#     "Cookie": "sessionid=bgdudos9yyspw9j9ai8j9upajpc8ry6m; csrftoken=9yTaANNzSkbd3QCuq61Sn936zG5mCN9u",
#     "Origin": "http://127.0.0.1:8000",
#     "Referer": "http://127.0.0.1:8000/ui/scrape-employees-data/fetch-employees",
#     "Sec-Fetch-Dest": "empty",
#     "Sec-Fetch-Mode": "cors",
#     "Sec-Fetch-Site": "same-origin",
#     "Sec-GPC": "1",
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
#     "X-CSRFToken": "4xss4X4FgIcejaPjBf7HdJV948thqhc23VbsuAH4YSdhcQhDRbYpqIO5tEotSUbm",
#     "sec-ch-ua": '"Brave";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": '"Windows"',
# }

# Data to be sent in the request body
data = {
    "auto": True,
    "job_titles": ["Technical Recruiter"],
    "locations": ["United States"],
}

for i in range(1, 1001):
# Make the POST request
    print("i: ", i)
    locations = data.get('locations', None)
    auto = data.get("auto", False)
    titles = data.get("job_titles", None)
    print("loctions, job_titles", locations, titles)
    # if titles is None or locations is None:
    #     return JsonResponse({"error": 'Job Titles or Locations are Missing'})
    # details = get_user_details(request.session.get('username'))
    # username = details['username']
    username="bhuvan304"
    print("finding user_entry.....")
    user_entry = apollo_apis_curl_collection.find_one({'username': username})
    print("found user_entry.....", user_entry)
    api_details = user_entry.get('apis', {})
    print("finding api_details.....")
    curl_request = api_details.get('api2', {}).get('curl_request')

    _data = {
         'person_titles': titles, 
         'person_locations': locations,
         'curl_request': curl_request
    }

    response = {'total_employees_fetched': 0}
    if auto:
        
        company = companies_collection.find_one({"is_processed": False})
        if not company:
            print({"error": "No unprocessed companies available"})
        company_id = company["id"]
        # print("company_id2", company_id)

        _data['organization_id'] = [company_id]
        
        print("Starting Fetching....")
        resp = fetch_employees_data_from_apollo(_data)
        if 'success' in resp:
            response['total_employees_fetched'] += resp['data']['count']
        else:
            response['error'] = resp
    # else:
    #     _data['organization_id'] = [company_info['id']]
    #     resp = fetch_employees_data_from_apollo(_data)
    #     if 'success' in resp:
    #         response['total_employees_fetched'] += resp['data']['count']
    #     else:
    #         response['error'] = resp
    print("response: ", response)
    if "error" in response:
        print(f"Error Occured at {i} th Company")
        break