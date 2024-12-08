import requests

from EmailWhiz.emailwhiz_api.views import fetch_employees_data_from_apollo
from pymongo import MongoClient

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
    # details = get_user_details(request.user)
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