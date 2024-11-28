
import copy
from django.shortcuts import render
from django.http import HttpResponse
from PyPDF2 import PdfReader
from django.conf import settings
from django.shortcuts import render, redirect
import traceback
from emailwhiz_api.email_sender import send_email
from .forms import ResumeSelectionForm, TemplateSelectionForm
import os
import requests
import shlex
import pytz
from itertools import combinations
from datetime import datetime
import math
import google.generativeai as genai
from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.core.mail import send_mail
from django.core.files.storage import FileSystemStorage
import json


from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')  # Replace with your MongoDB connection URI
db = client['EmailWhiz']  # Replace with your database name
companies_collection = db['companies'] 
and_collection = db['and_company_keywords']
combination_collection = db['combinations_company_keywords']
apollo_apis_curl_collection = db['apollo_apis_curl']
apollo_emails_collection = db['apollo_emails']

proxy = {
    "http": "http://User-001:123456@192.168.56.1:808",
    "https": "https://User-001:123456@192.168.56.1:808",
}

CustomUser = get_user_model()

# from dotenv import load_dotenv
# load_dotenv()


def get_template(details):
    template = '''Giving you my text of resume.\n
    {resume} 
    \n
    \n
    I want you to provide me a cold email template mail which I can send to a recruiter.\n
    For that try to extract details from specific sections of Resume Text  & it should include the following.\n
    \n
    1. Extract Skills - Use it in creating template in a separate paragraph.\n
    2. Template should contain information from work experience as well in a separate paragraph.\n
    3. Template should include why you are a good fit for the particular role.\n
    4. Use internet and search the internet about the company and add in the template (40 words) that why the candidate is inspired by the company's info in a separate paragraph.\n
    5. Add pursuing a degree if graduation done is False, else write completed  graduation: True.\n
    6. Don't include where I find the opportunity.\n
    7. The template should not contain [....] like thing. If possible search on internet.\n
    \n
    Also use the below critical information:\n
    \n
    1.First name of user: {first_name}\n 
    2. Last Name of user: {last_name}\n 
    3. University: {university}\n
    4. Target Company: {target_company}\n 
    5. Target role: {target_role}\n 
    6. Email: {email}\n
    7. Linkedln Profile: {linkedin_url}\n 
    8. Phone Number: {phone}\n
    9. Recruiter Name: {recruiter_name}\n
    10. Graduation Done: {graduation_done}\n
    11. Degree Name: {degree_name}\n
    \n
    \n
    I just want the body of the generated email template in response from your side as I want to use this in an API, so please give me only the body (without subject) in HTML. Please make sure to stick to the first 7 points & use the information from the critical information.'''

    return template.format(
    resume=details["resume"],
    first_name=details['first_name'],
    last_name=details["last_name"],
   university=details["university"],
    target_company=details['target_company'],
    target_role=details["target_role"],
    email=details["email"],
    linkedin_url=details['linkedin_url'],
    phone=details["phone_number"],
    recruiter_name=details["recruiter_name"],
    graduation_done=details['graduation_done'],
    degree_name=details["degree_name"])



def create_template_post(request):
    if request.method == 'POST':
        template_title = request.POST.get('template_title')
        template_content = request.POST.get('template_content')
        details= get_user_details(request.user)
        upload_dir = os.path.join(settings.MEDIA_ROOT, f'{details["username"]}/templates')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        # Define the path for the new template file
        template_path = os.path.join(upload_dir, f'{template_title}.txt')
        print("template_path: ", template_path)
        # Write content to the template file
        with open(template_path, 'w') as template_file:
            template_file.write(template_content)
            print("Hurrah!!")
        
        return redirect('home')  # Redirect to home or any success page

    return render(request, 'create_template.html')


def get_user_details(username):
    user = get_object_or_404(CustomUser, username=username)
    user_data = {
        "username": user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'university': user.college,
        'graduation_done': False if  user.graduated_or_not == 'no' else True,
        "email": user.email,
        "linkedin_url": user.linkedin_url,
        "phone_number": user.phone_number,
        "degree_name": user.degree_name,
        "gemini_api_key": user.gemini_api_key,
        "gmail_id": user.gmail_id,
        "gmail_in_app_password": user.gmail_in_app_password
    }
    return user_data





def save_resume(request):
    if request.method == 'POST':
        file_name = request.POST.get('file_name')
        uploaded_file = request.FILES.get('file')
        details= get_user_details(request.user)
        if uploaded_file:
            upload_dir = os.path.join(settings.MEDIA_ROOT, f'{details["username"]}/resumes')

            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            fs = FileSystemStorage(location=upload_dir)
            saved_file_name = file_name if file_name else uploaded_file.name

            saved_file_path = fs.save(f'{saved_file_name}.pdf', uploaded_file)

            return  render(request, 'base.html')


        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)



# def list_templates(request, user):
#     print("G1")
#     user_templates = os.listdir(f"/users/{user}/templates")
#     if request.method == "POST":
#         form = ResumeSelectionForm(request.POST, user_resumes=user_templates)
#         if form.is_valid():
#             selected_resume = form.cleaned_data['resume']
#             request.session['selected_resume'] = selected_resume  # Store selection in session
#             return redirect('select_template', user=user)
#     else:
#         form = ResumeSelectionForm(user_resumes=user_templates)
#     return render(request, 'myapp/list_resumes.html', {'form': form})

def list_templates(request):
    # Define the user directory where templates are stored
    user_directory = os.path.join('emailwhiz_api/users', request.user.username, 'templates')
    
    # Retrieve list of template files, if the directory exists
    templates = []
    if os.path.exists(user_directory):
        templates = [f for f in os.listdir(user_directory) if f.endswith('.txt')]
    
    return render(request, 'list_templates.html', {'templates': templates})

def list_resumes(request, user):
    print("G1")
    user_resumes = os.listdir(f"/users/{user}/resumes")
    if request.method == "POST":
        form = ResumeSelectionForm(request.POST, user_resumes=user_resumes)
        if form.is_valid():
            selected_resume = form.cleaned_data['resume']
            request.session['selected_resume'] = selected_resume  # Store selection in session
            return redirect('select_template', user=user)
    else:
        form = ResumeSelectionForm(user_resumes=user_resumes)
    return render(request, 'myapp/list_resumes.html', {'form': form})

# def select_template(request, user):
#     email_type = request.POST.get("template_type", "")
#     user_templates = os.listdir(f"/users/{user}/templates/{email_type}")
#     if request.method == "POST":
#         form = TemplateSelectionForm(request.POST, templates=user_templates)
#         if form.is_valid():
#             if form.cleaned_data['use_gemini']:
#                 # Call Gemini API here and save template choice
#                 pass
#             else:
#                 selected_template = form.cleaned_data['template_choice']
#                 request.session['selected_template'] = selected_template
#             return redirect('upload_excel', user=user)
#     else:
#         form = TemplateSelectionForm(templates=user_templates)
#     return render(request, 'myapp/select_template.html', {'form': form})


def upload_excel(request, user):
    if request.method == "POST":
        excel_file = request.FILES['excel']
        # Process Excel data and render table
        request.session['excel_data'] = ...  # Save processed data in session for preview
        return redirect('preview_template', user=user)
    return render(request, 'myapp/upload_excel.html')

def preview_template(request, user):
    selected_resume = request.session.get('selected_resume')
    selected_template = request.session.get('selected_template')
    excel_data = request.session.get('excel_data')
    if request.method == "POST":
        # Send the email here
        return redirect('success_page')
    return render(request, 'myapp/preview_template.html', {
        'resume': selected_resume,
        'template': selected_template,
        'excel_data': excel_data,
    })

def email_generator_post(request):
    print("Hello")
    if request.method == 'POST':

        details = get_user_details(request.user)
        gemini_api_key = details['gemini_api_key']

        
        print("Request Dict: ", request.__dict__)
        print("Details emails_generator_post: ", details)
        username = details['username']
        selected_resume = request.POST.get('resume')
        selected_template = request.POST.get('template')
        use_ai = request.POST.get("use_ai", "off") == "on"
        print("1use_ai", use_ai)
        resume_path = os.path.join(settings.MEDIA_ROOT, username, 'resumes', selected_resume)
        selected_template = request.POST.get('template')
        template_path = os.path.join(settings.MEDIA_ROOT, username, 'templates', selected_template)
        with open(template_path, 'r') as f:
            content = f.read()
        print("Resume_PATH: ", resume_path)
        # Extract text from the selected resume
        # extracted_text = extract_text_from_pdf(resume_path)
        # print("extracted_text: ", extracted_text)
        # # Create prompt for Gemini

        # details['resume'] = extracted_text

        data = []
        print(request.POST)
        rows = len(request.POST.getlist('first_name'))  # Get the number of rows
        print("rows", rows)
        resume = request.POST.get('resume')

        for i in range(rows):
            first_name = request.POST.getlist('first_name')[i]
            last_name = request.POST.getlist('last_name')[i]
            recruiter_email = request.POST.getlist('email')[i]
            target_company = request.POST.getlist('company')[i]
            target_role = request.POST.getlist('job_role')[i]
            
            _details = copy.deepcopy(details)
            
            _details['target_company'] = target_company
            _details['target_role'] = target_role
            _details['recruiter_email'] = recruiter_email
            _details['recruiter_name'] = first_name

            emp_data = {
                'first_name': first_name,
                'last_name': last_name,
                'email': recruiter_email,
                'company': target_company,
                'job_role': target_role,
                'resume_path': resume_path

            }

            # prompt = get_template(_details)
            print("2use_ai: ", use_ai)
            if use_ai:
                genai.configure(api_key=gemini_api_key)
                # Create the model
                generation_config = {
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
                }

                model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
                )

                prompt = f"""
                    I want to send a cold email to recruiter, and I want to use your response directly in the API.  I want you to generate an email based on the below template:\n\n 
                    {content}\n\n
                    \n\n Employer details are: \n
                    first_name: {emp_data['first_name']},\n
                    email: {emp_data['email']},\n
                    company: {emp_data['company']},\n
                    job_role: {emp_data['job_role']}\n
                    Few things you need to keep in mind:\n
                    1. I want you to fill up the values in all of the boxes []. Don't miss anyone of them. The response should not contain [....] like thing. If possible search on internet. \n 
                    2. I just want the content of the generated email template in response from your side as I want to use this in an API, so my application is totally dependent on you, so please give me only the content (without subject) in HTML format. \n 
                    3. I want your response as: <html><body>Email Body</body></html> & I want your response in the normal response text block, not in code block so that I can use your response in the API
                """      

                print("Prompt: ", prompt)      
                # Call Gemini API
                response = call_gemini_api(prompt, model)
                print("Response: ", response)
                emp_data['email_content'] = response.text
            else:
                message = content.format(first_name=first_name, last_name=last_name, email=recruiter_email, company_name=target_company, designation=target_role)
                emp_data['email_content'] = message
                
            data.append(emp_data)
        print("data: ", data)
        return render(request, 'view_generated_emails.html', {'data': data})
    else:
        return redirect('list_resumes')

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text += page.extract_text()
    except Exception as e:
        print(f"Error reading PDF: {e}")
    

    return text

def call_gemini_api(prompt, model):
    # url = "https://gemini-api-url.com/generate"  # Replace with actual Gemini API endpoint
    # headers = {"Authorization": "Bearer your_gemini_api_key", "Content-Type": "application/json"}
    # data = {"prompt": prompt}
    # return requests.post(url, json=data, headers=headers)
    
    
    chat_session = model.start_chat(
    history=[
    ]
    )

    response = chat_session.send_message(prompt)
    return response


def update_email_history(username, receiver_email, subject, content, company, designation):
    # Path to the user's directory
    user_dir = os.path.join(settings.MEDIA_ROOT, username)
    os.makedirs(user_dir, exist_ok=True)
    
    # Path to the history.json file
    history_file = os.path.join(user_dir, 'history.json')
    
    # Load or initialize the history data
    if os.path.exists(history_file):
        with open(history_file, 'r') as file:
            history_data = json.load(file)
    else:
        history_data = {"history": []}
    
# Define the US Eastern timezone

    # Get the current date in the US Eastern timezone
    date = datetime.now().strftime('%Y-%m-%d')

    # Find the recipient's history, or create a new one if it doesn't exist
    recipient_history = next((item for item in history_data["history"] if item["receiver_email"] == receiver_email), None)
    if recipient_history:
        recipient_history["emails"].append({"subject": subject, "content": content, "designation": designation,
            "date": date,})
    else:
        history_data["history"].append({
            "receiver_email": receiver_email,
            "company": company,
            "emails": [{"subject": subject, "content": content, "designation": designation, "date": date,}]
        })
    
    # Save the updated history data
    with open(history_file, 'w') as file:
        json.dump(history_data, file, indent=4)
def send_emails(request):
    print("123")
    if request.method == 'POST':
        details = get_user_details(request.user)
        data = json.loads(request.body).get('data')
        
        print("data", data)
        if not data:
            return JsonResponse({'error': 'No data provided'}, status=400)

        for employer in data:
            name = employer['first_name'] 
            receiver_email = employer['email']
            designation = employer['job_role']
            company_name = employer['company']
            message = employer['email_content']
            resume_path = employer['resume_path']
            subject = f"[{details['first_name']}]: Exploring {designation} Roles at {company_name}"
        
            send_email(details['gmail_id'], details['gmail_in_app_password'], receiver_email, subject, message, resume_path)
            update_email_history(details['username'], receiver_email, subject, message, company_name, designation)

    print("Success")
    return HttpResponse("success")
            


def generate_followup(request):
    if request.method == "POST":
        data = json.loads(request.body)
        receiver_email = data["receiver_email"]
        details= get_user_details(request.user)
        username = details['username']

        # Load email history
        user_dir = os.path.join(settings.MEDIA_ROOT, username)
        history_file = os.path.join(user_dir, 'history.json')
        with open(history_file, 'r') as file:
            history_data = json.load(file)

        # Get the last 2 emails
        recipient_history = next((item for item in history_data["history"] if item["receiver_email"] == receiver_email), None)
        if not recipient_history:
            return JsonResponse({"error": "No history found for this recipient."}, status=400)

        previous_emails = recipient_history["emails"][-2:] if len(recipient_history["emails"]) > 1 else recipient_history["emails"]
        prompt = "\n\n".join([f"Subject: {email['subject']}\nContent: {email['content']}" for email in previous_emails]) + """
        \n\nGenerate a follow-up email based on the above emails in HTML Format. I want to use your response in an API, so give me only the body as your response. \n 
        Give me the response as a json string which I can decode easily in my code for example: {'subject': 'Subject Generated', 'content': '<html><body>Email Body</body></html>'}\n
        I want your response in the normal response text block, not in code block so that I can use your response in the API.\n
        In your response, there should not be any boxes [mention something..]. I don't want to fill the values manuaaly not even date.\n
        Again, give me your response as text block in the format {.....} not in json or code block."""

        details = get_user_details(request.user)
        gemini_api_key = details['gemini_api_key']

        genai.configure(api_key=gemini_api_key)
        # Create the model
        generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        )
        print("Prompt: ", prompt)
        response = call_gemini_api(prompt, model)
        print("Response: ", response.text)
        if response.text[:7] == '```json':
            cleaned_resp = response.text[8:-4]
            print("cleaning..", cleaned_resp.find('{'))
        else:
            cleaned_resp = response.text
        print("Cleaned_resp: ", cleaned_resp)
        data = json.loads(cleaned_resp)
        print("Data: ", data)
        return JsonResponse({"subject": data["subject"], "content": data["content"]})
        


def send_followup(request):
    if request.method == "POST":
        details = get_user_details(request.user)
        username = details['username']
        data = json.loads(request.body)
        receiver_email = data["receiver_email"]
        content = data["content"]
        subject = data["subject"]

        send_email(details['gmail_id'], details['gmail_in_app_password'], receiver_email, subject, content, '')

        update_email_history(username, receiver_email, subject, content)
        return redirect('email_history')
        


def update_apollo_apis(request, api_name):

    details = get_user_details(request.user)
    username = details['username']
    
    # Ensure the collection has an entry for this user
    user_entry = apollo_apis_curl_collection.find_one({'username': username})
    if not user_entry:
        apollo_apis_curl_collection.insert_one({'username': username, 'apis': {}})

    if request.method == 'POST':
        curl_request = request.POST.get('curl_request')
        if not curl_request:
            return JsonResponse({'status': 'error', 'message': 'No curl request provided'}, status=400)

        # Update the API details for the specific user and API
        apollo_apis_curl_collection.update_one(
            {'username': username},
            {'$set': {f'apis.{api_name}.curl_request': curl_request}}
        )

    # Fetch updated API details
    user_entry = apollo_apis_curl_collection.find_one({'username': username})
    api_details = user_entry.get('apis', {})

    context = {
        'api1_value': api_details.get('api1', {}).get('curl_request', ''),
        'api2_value': api_details.get('api2', {}).get('curl_request', ''),
        'api3_value': api_details.get('api3', {}).get('curl_request', ''),
    }

    return render(request, 'update_apollo_apis.html', context)



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

def hit_apollo_api(request, api_name):
    details = get_user_details(request.user)
    username = details['username']
    user_entry = apollo_apis_curl_collection.find_one({'username': username})
    api_details = user_entry.get('apis', {})
    curl_request = api_details.get(api_name, {}).get('curl_request')
    if not curl_request:
        return JsonResponse({'error': f"No CURL request found for {api_name}"}, status=404)

    try:
        # Parse the curl command
        url, headers, data = parse_curl_command(curl_request)
        print("Data: ", data)
        if not url:
            return JsonResponse({'error': "Invalid CURL request: URL missing"}, status=400)

        # Perform the HTTP request
        if data:
            # print("Headers: ", headers)
            response = requests.post(url, headers=headers, data=data)
            print("R1: ", response, response.__dict__)
        else:
            response = requests.get(url, headers=headers)

        # Return the response in JSON format
        return JsonResponse(response.json(), safe=False)

    except Exception as e:
        return JsonResponse({'error': e}, status=500)
    


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

def get_companies_id(request, keywords, locations, requested_page, store_companies=False):
   

    details = get_user_details(request.user)
    username = details['username']
    user_entry = apollo_apis_curl_collection.find_one({'username': username})
    api_details = user_entry.get('apis', {})

    curl_request = api_details.get('api1', {}).get('curl_request')
    

    if not curl_request:
        return JsonResponse({'error': f"No CURL request found for Companies API"}, status=404)

    try:
        # Parse the curl command
        url, headers, data = parse_curl_command(curl_request)
        # data_json=json.loads(data)
        # print("Data1: ", data, type(data), len(data))
        
        data = replace_value_by_key(data, 'organization_locations', locations)
        data = replace_value_by_key(data, 'q_anded_organization_keyword_tags', keywords)
        data = replace_value_by_key(data, 'page', int(requested_page))
        data = replace_value_by_key(data, 'per_page', 25)
        # print("modified_json_string", data)
        # print("Data2: ", data, type(data))
        if not url:
            return JsonResponse({'error': "Invalid CURL request: URL missing"}, status=400)

        # Perform the HTTP request
        if data:
            # print("Headers: ", headers)
            all_companies = []
            response = requests.post(url, headers=headers, data=str(data))
            # print("R1: ", response, response.__dict__)
            response_data = response.json()
            # print("Response Data: ", response_data)
            accounts = response_data.get('accounts', [])
            organizations = response_data.get('organizations', [])

            for account in accounts:
                all_companies.append({
                    'name': account.get('name'),
                    'id': account.get('id'),
                    'logo_url': account.get('logo_url'),
                    'timestamp': datetime.now(),
                    'keywords': keywords,
                    'locations': locations
                })

            for organization in organizations:
                all_companies.append({
                    'name': organization.get('name'),
                    'id': organization.get('id'),
                    'logo_url': organization.get('logo_url'),
                    'timestamp': datetime.now(),
                    'keywords': keywords,
                    'locations': locations
                })

            companies_addition_count = 0
            if store_companies:
                if all_companies:
                    for company in all_companies:
                        # Check if the company already exists in the collection to avoid duplicates
                        result = companies_collection.update_one(
                            {'id': company['id']},  # Match document with the same ID
                            {
                                '$set': {
                                    'name': company['name'],
                                    'logo_url': company['logo_url'],
                                    'timestamp': datetime.now()
                                },
                                '$addToSet': {
                                    'keywords': {'$each': keywords},
                                    'locations': {'$each': locations}
                                },
                                '$setOnInsert': {
                                    'is_processed': False  # Set only if the document is newly created
                                }
                            },
                            upsert=True  # Create a new document if none exists
                        )
                        if result.modified_count == 0:
                            companies_addition_count += 1
                        # print(f"Modified: {result.modified_count}, Upserted: {result.upserted_id}, id: {company['id']}")
        

        # Return the response in JSON format
        resp = response.json()
        resp['companies_addition_count'] = companies_addition_count
        # print("Resp: ", resp)

        return resp

    except Exception as e:
        return JsonResponse({'error': response.__dict__['_content'].decode("utf-8")}, status=500)
    

def scrape_companies(request):
    
    try:
        data = json.loads(request.body)
        # new_keyword = data.get('keyword', '').strip()

        # if not new_keyword:
        #     return JsonResponse({'success': False, 'message': 'Invalid keyword'})
        locations = data.get("locations", [])

        if not locations:
            return JsonResponse({"error": "Locations are required"})
        # print("Hello.....")
        # Fetch an unprocessed combination
        combination = combination_collection.find_one({"is_processed": False})

        if not combination:
            return JsonResponse({"error": "No unprocessed combinations available"}, status=404)

        keywords = combination.get("keywords", [])
        # print("Keywords: ", keywords)
        response = get_companies_id(request, keywords, locations, 1)
        print("R1_response: ", response)
        total_entries = response['pagination']['total_entries']
        if total_entries > 125:
            total_pages = 5
        else:
            total_pages = math.ceil(total_entries/25)
        
        resp = {'companies_addition_count': 0}
        for i in range(1, total_pages+1):
            response = get_companies_id(request, keywords, locations, i, True)
            resp['companies_addition_count'] += response['companies_addition_count']
        # Mark the combination as processed
        combination_collection.update_one(
            {"_id": combination["_id"]},
            {"$set": {"is_processed": True}}
        )

        return JsonResponse({"success": resp, "keywords": keywords})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)
    


# def select_companies(request):
#     dataset = request.GET.get('dataset')
#     if not dataset:
#         return JsonResponse({'error': 'Dataset not selected'}, status=400)

#     details = get_user_details(request.user)
#     username = details['username']
#     user_dir = os.path.join(settings.MEDIA_ROOT, username, dataset)

#     with open(user_dir, 'r') as f:
#         companies = json.load(f)

#     return render(request, 'select_companies.html', {'companies': companies})

def fetch_employees_api(request):
    data = json.loads(request.body)
    company_name = data.get('company')
    employee_role = 'recruiter'  # Default role
    details = get_user_details(request.user)
    username = details['username']

    # Load API details
    api_details_path = os.path.join(settings.MEDIA_ROOT, username, 'apollo_apis_details.json')
    with open(api_details_path, 'r') as f:
        api_details = json.load(f)
    curl_request = api_details.get('api2', {}).get('curl_request')

    # Replace placeholders in the API call
    url, headers, payload = parse_curl_command(curl_request)
    payload = replace_value_by_key(payload, 'company_name', company_name)
    payload = replace_value_by_key(payload, 'employee_role', employee_role)
    print("payload: ", payload)
    response = requests.post(url, headers=headers, data=str(payload))

    # Save response data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    company_dir = os.path.join(settings.MEDIA_ROOT, username, 'employee_details', company_name)
    os.makedirs(company_dir, exist_ok=True)
    json_path = os.path.join(company_dir, f'{timestamp}.json')
    with open(json_path, 'w') as f:
        json.dump(response.json(), f, indent=4)

    return JsonResponse({'status': 'success'})




def add_keyword(request):
    if request.method == 'POST':
        try:
            # Parse the new keyword
            data = json.loads(request.body)
            new_keyword = data.get('keyword', '').strip()

            if not new_keyword:
                return JsonResponse({'success': False, 'message': 'Invalid keyword'})

            # Fetch the current keywords from `and_company_keywords`
            document = and_collection.find_one({})
            existing_keywords = document.get('keywords', []) if document else []

            # Add the new keyword to the list if it doesn't exist
            if new_keyword in existing_keywords:
                return JsonResponse({'success': False, 'message': 'Keyword already exists'})

            existing_keywords.append(new_keyword)
            and_collection.update_one({}, {'$set': {'keywords': existing_keywords}}, upsert=True)

            # Generate all combinations of the updated keywords
            all_combinations = []
            for r in range(1, len(existing_keywords) + 1):
                all_combinations.extend(combinations(existing_keywords, r))

            # Update the `combinations_company_keywords` collection
            combination_collection.delete_many({})  # Clear existing combinations
            new_combinations = [
                {'keywords': list(comb), 'is_processed': False}
                for comb in all_combinations
            ]
            combination_collection.insert_many(new_combinations)

            return JsonResponse({'success': True, 'message': 'Keyword added and combinations updated'})
        except Exception as e:
            print(f"Error adding keyword: {e}")
            return JsonResponse({'success': False, 'message': 'An error occurred'})


def get_keyword_combinations_counts(request):
    if request.method == 'GET':
        collection = db['combinations_company_keywords']
        total_processed = collection.count_documents({'is_processed': True})
        total_unprocessed = collection.count_documents({'is_processed': False})
        return JsonResponse({
            'processed': total_processed,
            'unprocessed': total_unprocessed
        })
    
def company_count(request):
    total = companies_collection.count_documents({})
    processed = companies_collection.count_documents({"is_processed": True})
    return JsonResponse({"total": total, "processed": processed})

def apollo_emails_count(request):
    total = apollo_emails_collection.count_documents({})
    unlocked_emails_count = apollo_emails_collection.count_documents({"email": {"$ne": ""}})
    return JsonResponse({"total": total, "unlocked_emails_count": unlocked_emails_count})


def employees_count(request):
    total = apollo_emails_collection.count_documents({})
    return JsonResponse({"total": total})


def get_non_processed_companies(request):
    companies = list(companies_collection.find({"is_processed": False}, {"_id": 0, "logo_url": 0}))
    # print("Companies: ", companies)
    return JsonResponse({'companies': companies}, safe=False)


def fetch_employees_data_from_apollo(_data):

    organization_id, person_titles, person_locations = _data['organization_id'],  _data['person_titles'],  _data['person_locations']
    

    curl_request = _data['curl_request']
    # print("curl_request: ", curl_request)

    if not curl_request:
        return JsonResponse({'error': f"No CURL request found for Employees API"}, status=404)

    try:
        # Parse the curl command
        url, headers, data = parse_curl_command(curl_request)
        
        if not url:
            return JsonResponse({'error': "Invalid CURL request: URL missing"}, status=400)

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

            
            # print("Body: ", data)
            # Perform the HTTP request
            response = requests.post(url, headers=headers, data=str(data))
            # print("R2: ", response.__dict__)
            response_data = response.json()

            people = response_data.get('people', [])
            if pages_found == False:
                total_entries = response_data['pagination']['total_entries']
                if total_entries > 125:
                    max_page = 3
                else:
                    max_page = math.ceil(total_entries/25)
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
                            "email_status": email_status
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


        # Mark organization as processed
        companies_collection.update_one(
            {'id': organization_id[0]},
            {'$set': {'is_processed': True}}
        )

        return {"success": True, "data": {'count': employees_addition_count}}

    except Exception as e:
        traceback.print_exc()
        return {'error': str(e)}
    


def fetch_employees(request):
    data = json.loads(request.body)
    company_info = data.get("company_id", None)
    # print("company_id: ", company_info)
    locations = data.get('locations', None)
    auto = data.get("auto", False)
    titles = data.get("job_titles", None)
    # print("loctions, job_titles", locations, titles)
    if titles is None or locations is None:
        return JsonResponse({"error": 'Job Titles or Locations are Missing'})
    details = get_user_details(request.user)
    username = details['username']
    user_entry = apollo_apis_curl_collection.find_one({'username': username})
    api_details = user_entry.get('apis', {})

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
            return JsonResponse({"error": "No unprocessed companies available"}, status=404)
        company_id = company["id"]
        # print("company_id2", company_id)

        _data['organization_id'] = [company_id]
        
        
        resp = fetch_employees_data_from_apollo(_data)
        if 'success' in resp:
            response['total_employees_fetched'] += resp['data']['count']
        else:
            response['error'] = 'Partial Success'
    else:
        _data['organization_id'] = [company_info['id']]
        resp = fetch_employees_data_from_apollo(_data)
        if 'success' in resp:
            response['total_employees_fetched'] += resp['data']['count']
        else:
            response['error'] = 'Could not fetch Employee Data'
    

    return JsonResponse({"data": response})


def search_companies(request):
    query = request.GET.get("query", "").strip()
    if len(query) < 3:
        return JsonResponse([], safe=False)  # Return empty list if query too short

    # Fetch matching companies
    matching_companies = companies_collection.find(
        {"name": {"$regex": query, "$options": "i"}},
        {"_id": 0, "id": 1, "name": 1, "logo_url": 1}
    )
    results = []

    for company in matching_companies:
        # Fetch the employee count for the current company
        employee_count = apollo_emails_collection.count_documents({"organization_id": company["id"]})
        emails_unlocked_count = apollo_emails_collection.count_documents({"organization_id": company["id"], "email": {"$ne": ""}})
        company["employees_count"] = employee_count
        company["emails_unlocked_count"] = emails_unlocked_count
        results.append(company)


    return JsonResponse(results, safe=False)



def fetch_employees_emails_from_apollo(_data):

    employee_ids = _data['employee_ids']
    # print("len: ", len(employee_ids), employee_ids)
    curl_request = _data['curl_request']

    if not curl_request:
        return JsonResponse({'error': f"No CURL request found for Employees API"}, status=404)

    try:
        # Parse the curl command
        url, headers, data = parse_curl_command(curl_request)
        
        if not url:
            return JsonResponse({'error': "Invalid CURL request: URL missing"}, status=400)

    
        data = replace_value_by_key(data, 'entity_ids', employee_ids)
        # print("Body2: ", data)
        response = requests.post(url, headers=headers, data=str(data))
        # print("R3: ", response.__dict__)
        response_data = response.json()

        contacts = response_data.get('contacts', [])


        emails_addition_count = 0
        for contact in contacts:
            employee_id = contact.get('person_id')
            employee_email = contact.get('email', '')
            # print("employee_email", employee_email)
            # Insert or update employee data in apollo_emails
            result = apollo_emails_collection.update_one(
                {'id': employee_id},
                {
                    '$set': {
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

def fetch_employees_emails(request):
    data = json.loads(request.body)
    company_info = data.get("company_id", None)
    # print("company_id: ", company_info)
    locations = data.get('locations', None)
    auto = data.get("auto", False)
    titles = data.get("job_titles", None)
    print("loctions, job_titles", locations, titles)
    if titles is None or locations is None:
        return JsonResponse({"error": 'Job Titles or Locations are Missing'})
    details = get_user_details(request.user)
    username = details['username']
    user_entry = apollo_apis_curl_collection.find_one({'username': username})
    api_details = user_entry.get('apis', {})

    curl_request = api_details.get('api3', {}).get('curl_request')

    _data = {
         'curl_request': curl_request
    }
    response = {'total_emails_fetched': 0}
    if auto:
        
        employee_details = apollo_emails_collection.find_one({"email": ''})
        # print("employee_details: ", employee_details)
        if not employee_details:
            return JsonResponse({"error": "All the Emails Have been fetched in our Database"})
        company_id = employee_details["organization_id"]
        # print("company_id: ", company_id)
        company_details = companies_collection.find_one({"id": company_id})
        company_name = company_details["name"]
        # print("company_id3", company_id)
        employee_ids = apollo_emails_collection.distinct("id", {
            "organization_id": company_id,
            "email": "",
            "titles": titles[0],
            "country": locations[0]
        })

    else:
        employee_ids = apollo_emails_collection.distinct("id", {
            "organization_id": company_info['id'],
            "email": "",
            "titles": titles,
            "country": locations
        })
        company_name = company_info['name']
    batches = math.ceil(len(employee_ids)/10)
    # batches = 1
    batch_size = 10
    # batch_size = 1
    print("batches: ", batches)
    current_batch = 1
    start_index = 0
    while current_batch<=batches:
        if current_batch == batches:
            _data['employee_ids'] = employee_ids[start_index: ]
        else:
            _data['employee_ids'] = employee_ids[start_index: current_batch*batch_size]

    
        resp = fetch_employees_emails_from_apollo(_data)
        if 'success' in resp:
            
            start_index = current_batch*batch_size
            current_batch += 1
            response['total_emails_fetched'] += resp['data']['count']
        else:
            response['error'] = 'Partial Success'
            break
    
    response["company"] = company_name
    return JsonResponse({"data": response})