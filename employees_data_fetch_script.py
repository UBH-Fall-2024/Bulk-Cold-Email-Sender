import requests

# URL to send the request to
url = "http://0.0.0.0:8000/api/fetch-employees/"

# Headers for the request
headers = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Cookie": "sessionid=bgdudos9yyspw9j9ai8j9upajpc8ry6m; csrftoken=9yTaANNzSkbd3QCuq61Sn936zG5mCN9u",
    "Origin": "http://127.0.0.1:8000",
    "Referer": "http://127.0.0.1:8000/ui/scrape-employees-data/fetch-employees",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-GPC": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "X-CSRFToken": "4xss4X4FgIcejaPjBf7HdJV948thqhc23VbsuAH4YSdhcQhDRbYpqIO5tEotSUbm",
    "sec-ch-ua": '"Brave";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# Data to be sent in the request body
data = {
    "auto": True,
    "job_titles": ["Technical Recruiter"],
    "locations": ["United States"],
}

for i in range(1, 1001):
# Make the POST request
    print("i: ", i)
    response = requests.post(url, headers=headers, json=data)

    # Print the response
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(response.text)
