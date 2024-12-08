import math
import shlex
import time
import traceback
from pymongo import MongoClient
import requests
from datetime import datetime

client = MongoClient('mongodb+srv://shoaibthakur23:Shoaib%40345@cluster0.xjugu.mongodb.net/')  # Replace with your MongoDB connection URI
db = client['EmailWhiz']  # Replace with your database name
companies_collection = db['companies'] 
and_collection = db['and_company_keywords']
subject_collection = db['subjects']
combination_collection = db['combinations_company_keywords']
apollo_apis_curl_collection = db['apollo_apis_curl']
apollo_emails_collection = db['apollo_emails']
apollo_emails_sent_history_collection = db['apollo_emails_sent_history']




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



def fetch_employees_emails_from_apollo(_data):

    employee_ids = _data['employee_ids']
    organization_id = _data['organization_id']
    # print("len: ", len(employee_ids), employee_ids)
    curl_request = _data['curl_request']

    if not curl_request:
        return print({'error': f"No CURL request found for Employees API"})

    try:
        # Parse the curl command
        url, headers, data = parse_curl_command(curl_request)
        
        if not url:
            return print({'error': "Invalid CURL request: URL missing"})

    
        data = replace_value_by_key(data, 'entity_ids', employee_ids)
        # print("Body2: ", data)
        response = requests.post(url, headers=headers, data=str(data))
        if response.status_code == 401: 
                return {"error": response.__dict__["_content"].decode('utf-8')}
        # print("R3: ", response.__dict__)
        response_data = response.json()
            # print("R2.1: ", response_data)
        if response.status_code != 200: 
            return response_data
        contacts = response_data.get('contacts', [])


        emails_addition_count = 0
        for contact in contacts:
            employee_id = contact.get('person_id')
            employee_email = contact.get('email', '')
            employee_org_id = contact.get("organization_id", organization_id)
            # print("employee_email", employee_email)
            # Insert or update employee data in apollo_emails
            result = apollo_emails_collection.update_one(
                {'id': employee_id},
                {
                    '$set': {
                        'organization_id': employee_org_id,
                        'email': employee_email,
                    }
                },
                upsert=True
            )
            if result.modified_count:
                emails_addition_count += 1


        return {"success": True, "data": {'count': emails_addition_count}}

    except Exception as e:
        traceback.print_exc()
        return {'error': str(e)}

# Data to be sent in the request body
data = {
    "auto": True,
    "job_titles": ["Technical Recruiter"],
    "locations": ["United States"],
}

for i in range(1, 2):
    print(f"{i}th Attempt")
    # data = json.loads(request.body)
    # company_info = data.get("company_id", None)
    # print("company_id: ", company_info)
    locations = data.get('locations', None)
    auto = data.get("auto", False)
    titles = data.get("job_titles", None)
    print("loctions, job_titles", locations, titles)
    if titles is None or locations is None:
        print({"error": 'Job Titles or Locations are Missing'})
    # details = get_user_details(request.user)
    # username = details['username']
    username='shoaib231'
    user_entry = apollo_apis_curl_collection.find_one({'username': username})
    api_details = user_entry.get('apis', {})

    curl_request = api_details.get('api3', {}).get('curl_request')

    _data = {
         'curl_request': curl_request
    }
    response = {'total_emails_fetched': 0}
    if auto:
        print("Inside Auto...")
        employee_details = apollo_emails_collection.find_one({
            "email": "",
            "titles": {"$in": titles},
            "country": locations[0]
        })
        print("employee_details: ", employee_details)
        if not employee_details:
            print({"error": "All the Emails Have been fetched in our Database"})
            break
        company_id = employee_details["organization_id"]
        # print("company_id: ", company_id)
        company_details = companies_collection.find_one({"id": company_id})
        company_name = company_details["name"]
        print("company_details", company_details, titles[0], locations[0])
        employee_ids = apollo_emails_collection.distinct("id", {
            "organization_id": company_id,
            "email": "",
            "titles": {"$in": titles},
            "country": locations[0]
        })

    # else:
    #     employee_ids = apollo_emails_collection.distinct("id", {
    #         "organization_id": company_info['id'],
    #         "email": "",
    #         "titles": titles,
    #         "country": locations
    #     })
    #     company_name = company_info['name']
    print("len(employee_ids): ", len(employee_ids))
    batches = math.ceil(len(employee_ids)/5)
    # batches = 1
    batch_size = 5
    # batch_size = 1
    print("batches: ", batches)
    current_batch = 1
    start_index = 0
    while current_batch<=batches:
        if current_batch == batches:
            _data['employee_ids'] = employee_ids[start_index: ]
        else:
            _data['employee_ids'] = employee_ids[start_index: current_batch*batch_size]

        _data['organization_id'] = company_id
        print("Start Fetching.....")
        resp = fetch_employees_emails_from_apollo(_data)
        print("Sleep Started..", datetime.now())
        time.sleep(80)
        print("Sleep Ended..", datetime.now())
        if 'success' in resp:
            
            start_index = current_batch*batch_size
            current_batch += 1
            response['total_emails_fetched'] += resp['data']['count']
        else:
            response['error'] = resp
            break
    
    response["company"] = company_name
    print("Response: ", response)
    if "error" in response:
        print("Response: Error: ", response)
        break