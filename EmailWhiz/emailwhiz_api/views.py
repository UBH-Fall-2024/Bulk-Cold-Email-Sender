
from concurrent.futures import ThreadPoolExecutor
import copy
import uuid
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
import datetime as dt
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

from django.views.decorators.csrf import csrf_exempt
import time
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import get_user_model

# from .models import CustomMongoDBUser
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate

from django.conf import settings

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
users_collection = db['users'] 


CustomUser = get_user_model()
SECRET_KEY = 'EmailWhiz'
# from dotenv import load_dotenv
# load_dotenv()


def get_user_details(username):
    user = users_collection.find_one({"username": username}, {"_id": 0, "password": 0})
    if user:
        user['graduation_done'] = False if  user["graduated_or_not"] == 'no' else True,
        return user
    return {"error": "User not found."}

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
        details= get_user_details(request.session.get('username'))
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


# def get_user_details(username):
#     user = get_object_or_404(CustomUser, username=username)
#     user_data = {
#         "username": user.username,
#         'first_name': user.first_name,
#         'last_name': user.last_name,
#         'university': user.college,
#         'graduation_done': False if  user.graduated_or_not == 'no' else True,
#         "email": user.email,
#         "linkedin_url": user.linkedin_url,
#         "phone_number": user.phone_number,
#         "degree_name": user.degree_name,
#         "gemini_api_key": user.gemini_api_key,
#         "gmail_id": user.gmail_id,
#         "gmail_in_app_password": user.gmail_in_app_password
#     }
#     return user_data


def get_user_details(username):
    """
    Fetches user details from MongoDB for a given username.

    Args:
        username (str): The username of the user.

    Returns:
        dict: A dictionary containing user details if found.

    Raises:
        ValueError: If the user is not found in the database.
    """
    # Query MongoDB to find the user
    user = users_collection.find_one({"username": username})
    
    if not user:
        # Raise an error if the user is not found
        raise ValueError(f"User with username '{username}' not found.")
    
    # Construct the user data dictionary
    user_data = {
        "username": user.get("username"),
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "university": user.get("college"),
        "graduation_done": user.get("graduated_or_not", "").lower() != 'no',  # Graduation status
        "email": user.get("email"),
        "linkedin_url": user.get("linkedin_url"),
        "phone_number": user.get("phone_number"),
        "degree_name": user.get("degree_name"),
        "gemini_api_key": user.get("gemini_api_key"),
        "gmail_id": user.get("gmail_id"),
        "gmail_in_app_password": user.get("gmail_in_app_password"),
    }

    return user_data

def save_resume(request):
    if request.method == 'POST':
        file_name = request.POST.get('file_name')
        uploaded_file = request.FILES.get('file')
        details= get_user_details(request.session.get('username'))
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

        details = get_user_details(request.session.get('username'))
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
        details = get_user_details(request.session.get('username'))
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
            subject = f"[{details['first_name']} {details['last_name']}]: Exploring {designation} Roles at {company_name}"
        
            send_email(details['gmail_id'], details['gmail_in_app_password'], receiver_email, subject, message, resume_path)
            update_email_history(details['username'], receiver_email, subject, message, company_name, designation)

    print("Success")
    return HttpResponse("success")
            


def generate_followup(request):
    if request.method == "POST":
        data = json.loads(request.body)
        receiver_email = data["receiver_email"]
        details= get_user_details(request.session.get('username'))
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

        details = get_user_details(request.session.get('username'))
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
        details = get_user_details(request.session.get('username'))
        username = details['username']
        data = json.loads(request.body)
        receiver_email = data["receiver_email"]
        content = data["content"]
        subject = data["subject"]

        send_email(details['gmail_id'], details['gmail_in_app_password'], receiver_email, subject, content, '')

        update_email_history(username, receiver_email, subject, content)
        return redirect('email_history')
        


def update_apollo_apis(request, api_name):

    details = get_user_details(request.session.get('username'))
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
    details = get_user_details(request.session.get('username'))
    username = details['username']
    # print("username: ", username)
    entry = apollo_apis_curl_collection.find_one({'username': username})
    # print("entry: ", entry)
    api_details = entry.get('apis', {})
    curl_request = api_details.get(api_name, {}).get('curl_request')
    if not curl_request:
        return JsonResponse({'error': f"No CURL request found for {api_name}"})

    try:
        # Parse the curl command
        url, headers, data = parse_curl_command(curl_request)
        # print("Data: ", data)
        if not url:
            return JsonResponse({'error': "Invalid CURL request: URL missing"})

        # Perform the HTTP request
        if data:
            # print("Headers: ", headers)
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 401: 
                return JsonResponse({"error": response.__dict__["_content"].decode('utf-8')})
            print("R1: ", response, response.__dict__)
        else:
            response = requests.get(url, headers=headers)
        print("response.status_code: ", response.status_code)
        if response.status_code == 401:
            # print('response.__dict__["_content"]', response.__dict__["_content"])
            return JsonResponse({"error": response.__dict__["_content"].decode('utf-8')}, safe=False)
        # Return the response in JSON format
        return JsonResponse(response.json(), safe=False)

    except Exception as e:
        return JsonResponse({'error': e})
    


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
   

    details = get_user_details(request.session.get('username'))
    username = details['username']
    user_entry = apollo_apis_curl_collection.find_one({'username': username})
    api_details = user_entry.get('apis', {})

    curl_request = api_details.get('api1', {}).get('curl_request')
    

    if not curl_request:
        return {'error': f"No CURL request found for Companies API"}

    try:
        # Parse the curl command
        url, headers, data = parse_curl_command(curl_request)
        # data_json=json.loads(data)
        # print("Data1: ", data, type(data), len(data))
        print("keywords: ", keywords)
        data = replace_value_by_key(data, 'organization_locations', locations)
        data = replace_value_by_key(data, 'q_anded_organization_keyword_tags', keywords)
        data = replace_value_by_key(data, 'page', int(requested_page))
        data = replace_value_by_key(data, 'per_page', 25)
        # print("modified_json_string", data)
        # print("Data2: ", data, type(data))
        if not url:
            return {'error': "Invalid CURL request: URL missing"}

        # Perform the HTTP request
        if data:
            # print("Headers: ", headers)
            all_companies = []
            response = requests.post(url, headers=headers, data=str(data))
            # print("R1: ", response, response.__dict__)
            if response.status_code == 401: 
                return {"error": response.__dict__["_content"].decode('utf-8')}
            response_data = response.json()
            if response.status_code != 200: 
                return {"error": response_data}
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
        traceback.print_exc()
        return {'error': e}
    

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
        print("combination: ", combination)
        if not combination:
            return JsonResponse({"error": "No unprocessed combinations available"})

        keywords = combination.get("keywords", [])
        print("Keywords: ", keywords)
        response = get_companies_id(request, keywords, locations, 1)
        print("R1_response: ", response)
        if "error" in response:
            return JsonResponse({"error": response})
        total_entries = response['pagination']['total_entries']
        if total_entries > 125:
            total_pages = 5
        else:
            total_pages = math.ceil(total_entries/25)
        
        resp = {'companies_addition_count': 0}
        for i in range(1, total_pages+1):
            response = get_companies_id(request, keywords, locations, i, True)
            resp['companies_addition_count'] += response['companies_addition_count']
            print("Sleep Started..", datetime.now())
            time.sleep(60)
            print("Sleep Ended..", datetime.now())
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

#     details = get_user_details(request.session.get('username'))
#     username = details['username']
#     user_dir = os.path.join(settings.MEDIA_ROOT, username, dataset)

#     with open(user_dir, 'r') as f:
#         companies = json.load(f)

#     return render(request, 'select_companies.html', {'companies': companies})





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
    print(datetime.now().astimezone(dt.timezone.utc))
    
    total = apollo_emails_collection.count_documents({})
    unlocked_emails_count = apollo_emails_collection.count_documents({"email": {"$ne": ""}})
    return JsonResponse({"total": total, "unlocked_emails_count": unlocked_emails_count})


def emails_sent_count(request):
    total = apollo_emails_collection.count_documents({})
    # Get current system time and convert to UTC
    now = datetime.now()

    # Calculate the start and end of today in UTC
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + dt.timedelta(days=1)
    print("total_start", today_start, "today_end", today_end)
    

    # Count the documents
    # today_emails_sent_count = today_entries.count()
    today_emails_sent_count = apollo_emails_sent_history_collection.count_documents(
    {"emails.timestamp": {"$gte": today_start, "$lt": today_end}}
)
    
    unlocked_emails_count = apollo_emails_collection.count_documents({"email": {"$ne": ""}})
    total_sent_emails = apollo_emails_sent_history_collection.count_documents({})
    print("today_emails_sent_count, total_sent_emails", today_emails_sent_count, total_sent_emails)
    return JsonResponse({"total": total, "unlocked_emails_count": unlocked_emails_count, "total_sent_emails": total_sent_emails, "today_emails_sent_count": today_emails_sent_count})


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

@csrf_exempt
def fetch_employees(request):

    data = json.loads(request.body)
    company_info = data.get("company_id", None)
    # print("company_id: ", company_info)
    locations = data.get('locations', None)
    auto = data.get("auto", False)
    titles = data.get("job_titles", None)
    print("loctions, job_titles", locations, titles)
    if titles is None or locations is None:
        return JsonResponse({"error": 'Job Titles or Locations are Missing'})
    details = get_user_details(request.session.get('username'))
    username = details['username']
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
            return JsonResponse({"error": "No unprocessed companies available"}, status=404)
        company_id = company["id"]
        # print("company_id2", company_id)

        _data['organization_id'] = [company_id]
        
        print("Starting Fetching....")
        resp = fetch_employees_data_from_apollo(_data)
        if 'success' in resp:
            response['total_employees_fetched'] += resp['data']['count']
        else:
            response['error'] = resp
    else:
        _data['organization_id'] = [company_info['id']]
        resp = fetch_employees_data_from_apollo(_data)
        if 'success' in resp:
            response['total_employees_fetched'] += resp['data']['count']
        else:
            response['error'] = resp
    
    # if "error" in response:
    #     return JsonResponse({"error": True, "data": response})
    return JsonResponse(response)


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
        verified_emails_count = apollo_emails_sent_history_collection.count_documents({"email_status": "verified"})
        # emails_sent_count = apollo_emails_sent_history_collection.count_documents({})
        already_emails_sent_count = apollo_emails_sent_history_collection.count_documents({"organization_id": company["id"]})

        company["employees_count"] = employee_count
        company["emails_unlocked_count"] = emails_unlocked_count
        company["verified_emails_count"] = verified_emails_count
        # company["emails_sent_count"] = emails_sent_count
        company["already_emails_sent_count"] = already_emails_sent_count
        

        results.append(company)

    # print("results: ", results)
    return JsonResponse(results, safe=False)



def fetch_employees_emails_from_apollo(_data):

    employee_ids = _data['employee_ids']
    # print("len: ", len(employee_ids), employee_ids)
    curl_request = _data['curl_request']

    if not curl_request:
        return {'error': f"No CURL request found for Employees API"}

    try:
        # Parse the curl command
        url, headers, data = parse_curl_command(curl_request)
        
        if not url:
            return {'error': "Invalid CURL request: URL missing"}

        print("Body 1: ", data)
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



def unlock_emails_job(data):
    username = data['username']
    locations = data.get('locations', None)
    auto = data.get("auto", False)
    titles = data.get("job_titles", None)
    number_of_companies = data.get("number_of_companies")
    company_info = data.get("company_info")
    curl_request = data.get("curl_request")

    jobs = db['jobs']
    job_id = str(uuid.uuid4())
    job_document = {
        "job_name": "unlock_emails_job",
        "total": number_of_companies,
        "completed": 0,
        "latest_log": "Started",
        "status": "running",
        "id": job_id,
        "username": username,
        "created_at": datetime.now()  # Add created_at field
    }
    jobs.insert_one(job_document)

    if auto == False:
        number_of_companies = 1
    apollo_emails_collection = db['apollo_emails']
    total_emails = 0
    for i in range(1, number_of_companies + 1):
        print(f"Starting {i}th Company", auto)
        print("Titles: ", titles)
        print("Locations: ", locations)

        response = {'total_emails_fetched': 0}
        if auto:
            print("G1")
            print("Titles: ", titles)
            print("Locations: ", locations)

            employee_details = apollo_emails_collection.find_one({
                "email": "",
                "titles": {"$in": titles},
                "country": locations[0]
            })
            print("G2", employee_details)
            print("employee_details: ", employee_details)
            
            if not employee_details:
                jobs.update_one(
                    {"id": job_id},
                    {"$set": {"status": "error", "latest_log": str({"error": "All the Emails Have been fetched in our Database"})}}
                )
                return
            print("G3")
            company_id = employee_details["organization_id"]
            # print("company_id: ", company_id)
            company_details = companies_collection.find_one({"id": company_id})
            company_name = company_details["name"]
            print("company_details", company_details)
            employee_ids = apollo_emails_collection.distinct("id", {
                "organization_id": company_id,
                "email": "",
                "titles": {"$in": titles},
                "country": locations[0]
            })
            print("G4", employee_ids)

        else:
            employee_ids = apollo_emails_collection.distinct("id", {
                "organization_id": company_info['id'],
                "email": "",
                "titles": {"$in": titles},
                "country": locations[0]
            })
            print("T2", employee_ids)
            company_name = company_info['name']
        
        batch_size = 2
        batches = math.ceil(len(employee_ids)/2)
        print("batches: ", batches)
        current_batch = 1
        start_index = 0
        _data = {
            'curl_request': curl_request
        }
        while current_batch<=batches:
            if current_batch == batches:
                _data['employee_ids'] = employee_ids[start_index: ]
            else:
                _data['employee_ids'] = employee_ids[start_index: current_batch*batch_size]

        
            resp = fetch_employees_emails_from_apollo(_data)
            print("Sleep Started..", datetime.now())
            time.sleep(120)
            print("Sleep Ended..", datetime.now())
            if 'success' in resp:
                start_index = current_batch*batch_size
                current_batch += 1
                response['total_emails_fetched'] += resp['data']['count']
                total_emails += resp['data']['count']
                if total_emails >= 500:
                    print("Day Sleep Started.. 26400 Seconds", datetime.now())
                    jobs.update_one(
                        {"id": job_id},
                        {"$set": {"latest_log": f"Deep Sleep {i}th Company: {str(response)} | Completed Batch {current_batch} | Total Emails Crossed 500: {total_emails}"}}
                    )
                    time.sleep(26400)
                    total_emails = 0
                    print("Day Sleep Ended.. 26400 Seconds", datetime.now())
                
                jobs.update_one(
                    {"id": job_id},
                    {"$set": {"latest_log": f"Processesing {i}th Company: {str(response)} | Completed Batch {current_batch}"}}
                )
            else:
                response['error'] = resp
                jobs.update_one(
                    {"id": job_id},
                    {"$set": {"status": "error", "latest_log": str(response)}}
                )
                return
        
        response["company"] = company_name

        jobs.update_one(
            {"id": job_id},
            {"$set": {"completed": i, "latest_log": f"Processed {i}th Company: {str(response)}"}}
        )
        
        
    # Mark the job as completed
    jobs.update_one(
        {"id": job_id},
        {"$set": {"status": "completed", "latest_log": "Job completed. All the Companies have been processed"}}
    )
    print(f"Job {job_id} completed")

def fetch_employees_emails(request):
    jobs = db['jobs']
    details = get_user_details(request.session.get('username'))
    username = details['username']
    data = json.loads(request.body)
    company_info = data.get("company_id", None)
    # print("company_id: ", company_info)
    locations = data.get('locations', None)
    auto = data.get("auto", False)
    titles = data.get("job_titles", None)
    number_of_companies = data.get("number_of_companies", 1)

    print("loctions, job_titles", locations, titles)

    if titles is None or locations is None:
        return JsonResponse({"error": 'Job Titles or Locations are Missing'})
    entry = apollo_apis_curl_collection.find_one({'username': username})
    api_details = entry.get('apis', {})
    curl_request = api_details.get('api3', {}).get('curl_request')
    
    
    
    existing_job = jobs.find_one({"username": username, "status": "running"})
    if existing_job:
        return JsonResponse({
            "error": f"A job of type 'f{existing_job['id']}' is already running for this user. Please wait for it to complete."
        })
    executor = ThreadPoolExecutor(max_workers=5)
    temp_data = {
        'username': username, 
        'company_info': company_info,
        'locations': locations, 
        'auto': auto,
        'job_titles': titles,
        'number_of_companies': number_of_companies,
        'curl_request': curl_request
    }
    executor.submit(unlock_emails_job, temp_data)

    # Return an immediate response
    return JsonResponse({"success": True, "message": "Job has started"})

    
    

    
    


def send_cold_emails_by_automation_through_apollo_emails(request):
    try:
        data = json.loads(request.body)
        details = get_user_details(request.session.get('username'))
        username = details['username']
        # print("company_id: ", company_info)
        locations = data.get('locations', None)
        job_titles = data.get("job_titles", None)
        target_role = data.get("target_role", None)
        selected_template = data.get("selected_template", None)
        selected_subject = data.get("selected_subject", None)
        resume_name = data.get("selected_resume", None)
        print("loctions, job_titles, target_role, selected_template, resume_name, selected_subject", locations, job_titles, target_role, selected_template, resume_name, selected_subject)
        if selected_subject:
            temp_subject = subject_collection.find_one({"username": username}, {"_id": 0, "subject_title": 1, "subject_content": 1})
            # print("subject: ", temp_subject)
        employees = apollo_emails_collection.find({
            "titles": {"$in": job_titles},
            "country": {"$in": locations},
            "email": {"$exists": True, "$ne": ""},
            # "email_status": "verified"
            })

        # Filter employees whose entries are not in apollo_emails_sent_history for the target_role
        employee_details = None
        for employee in employees:
            existing_history = apollo_emails_sent_history_collection.find_one({
                "person_id": employee["id"],
                "organization_id": employee["organization_id"],
                "emails.target_role": target_role,
            })
            if not existing_history:
                employee_details = employee
                break
        if not employee_details:
            return JsonResponse({"error": f"Unable to send Emails as None Emails are Filtered according to your input or All the Emails for your input have been already sent OR There are No Emails which are Unlocked.", "count": 0})
        
        receiver_first_name = employee_details["first_name"]
        receiver_last_name = employee_details["last_name"]
        employee_email = employee_details["email"]
        organization_id = employee_details["organization_id"]
        company_details = companies_collection.find_one({"id": organization_id})
        company_name = company_details["name"]
        
        existing_email_history = apollo_emails_sent_history_collection.find_one(
            {
                "person_id": employee_details["id"],
                "organization_id": organization_id,
                "emails.target_role": target_role,
            }
        )
        if existing_email_history:
            return JsonResponse({"error": f"Email already sent to the {employee_email} for the target role: {target_role}" })
        subject_details = {
            'first_name': details['first_name'], 
            'last_name': details['last_name'],
            'target_role': target_role, 
            'company_name': company_name
        }
        # print("Subect Details: ", subject_details)

        subject = temp_subject["subject_content"]
        for variable in ['first_name', 'last_name', 'target_role', 'company_name']:
            if variable in subject and variable in subject_details:
                # print("subject_details[variable]: ", subject_details[variable])
                subject = subject.replace("{" + variable + "}", subject_details[variable])
                # print("S: ", subject)

        print("subject2: ", subject)
        # subject = f"[{details['first_name']} {details['last_name']}]: Exploring {target_role} Roles at {company_name}"
        template_path = os.path.join(settings.MEDIA_ROOT, username, 'templates', selected_template)
        with open(template_path, 'r') as f:
            content = f.read()
        resume_path = os.path.join(settings.MEDIA_ROOT, username, 'resumes', resume_name)

        personalized_message = content.format(first_name=receiver_first_name, last_name=receiver_last_name, email=employee_email, company_name=company_name, designation=target_role)
        send_email(details['gmail_id'], details['gmail_in_app_password'], employee_email, subject, personalized_message, resume_path)
        time.sleep(0.25)
        existing_entry = apollo_emails_sent_history_collection.find_one(
            {"person_id": employee_details["id"], "organization_id": organization_id}
        )

        new_email_entry = {
            "subject": subject,
            "content": personalized_message,
            "target_role": target_role,
            "timestamp": datetime.now(),
        }

        if existing_entry:
            # Append the new email entry to the existing emails array
            apollo_emails_sent_history_collection.update_one(
                {"_id": existing_entry["_id"]},
                {"$push": {"emails": new_email_entry}}
            )
            print("Entry Exist, We have started pushing.....")
        else:
            # Create a new document if no history exists
            email_history_entry = {
                "person_id": employee_details["id"],
                "receiver_email": employee_email,
                "company": company_name,
                "organization_id": organization_id,
                "emails": [new_email_entry],
            }
            apollo_emails_sent_history_collection.insert_one(email_history_entry)

        return JsonResponse({"success": f"Sent Successfully: {employee_email}"})
    except Exception as exc:
        traceback.print_exc()
        return JsonResponse({"error": f"{exc}"})



def send_cold_emails_by_company_through_apollo_emails(request):
    try:
        data = json.loads(request.body)
        details = get_user_details(request.session.get('username'))
        username = details['username']
        company_info = data.get("company_id", None)
        # print("company_id: ", company_info)
        locations = data.get('locations', None)
        job_titles = data.get("job_titles", None)
        target_role = data.get("target_role", None)
        selected_template = data.get("selected_template", None)
        selected_subject = data.get("selected_subject", None)
        resume_name = data.get("selected_resume", None)
        print("loctions, job_titles, target_role, company_info, selected_template, resume_name, selected_subject", locations, job_titles, target_role, company_info, selected_template, resume_name, selected_subject)
        if selected_subject:
            temp_subject = subject_collection.find_one({"username": username}, {"_id": 0, "subject_title": 1, "subject_content": 1})
            # print("subject: ", temp_subject)
            
        employees = apollo_emails_collection.find({
            "organization_id": company_info["id"],
            "titles": {"$in": job_titles},
            "country":{"$in": locations},
            "email": {"$exists": True, "$ne": ""},
            # "email_status": "verified"
            })

        employee_count = apollo_emails_collection.count_documents({
            "organization_id": company_info["id"],
            "titles": {"$in": job_titles},
            "country": {"$in": locations},
            # "email_status": "verified"
        })
        print("employees: ", employees, employee_count)
        # Filter employees whose entries are not in apollo_emails_sent_history for the target_role
        filtered_employees = []
        for employee in employees:
            print("E: ", employee)
            existing_history = apollo_emails_sent_history_collection.find_one({
                "person_id": employee["id"],
                "organization_id": employee["organization_id"],
                "emails.target_role": target_role,
            })
            if not existing_history:
                filtered_employees.append(employee)

        if not filtered_employees:
            return JsonResponse({"error": f"Unable to send Emails as None Emails are Filtered according to your input or All the Emails for your input have been already sent OR There are No Emails which are Unlocked.", "count": 0})
        
        count = 0
        for employee in filtered_employees:
            receiver_first_name = employee["first_name"]
            receiver_last_name = employee["last_name"]
            employee_email = employee["email"]
            organization_id = employee["organization_id"]
            company_name = company_info["name"]
            subject_details = {
            'first_name': details['first_name'], 
            'last_name': details['last_name'],
            'target_role': target_role, 
            'company_name': company_name
            }
            subject = temp_subject["subject_content"]
            for variable in ['first_name', 'last_name', 'target_role', 'company_name']:
                if variable in subject and variable in subject_details:
                    # print("subject_details[variable]: ", subject_details[variable])
                    subject = subject.replace("{" + variable + "}", subject_details[variable])
                    # print("S: ", subject)
            print("subject2: ", subject)
            # subject = f"[{details['first_name']} {details['last_name']}]: Exploring {target_role} Roles at {company_name}"
            template_path = os.path.join(settings.MEDIA_ROOT, username, 'templates', selected_template)
            with open(template_path, 'r') as f:
                content = f.read()
            resume_path = os.path.join(settings.MEDIA_ROOT, username, 'resumes', resume_name)

            personalized_message = content.format(
                first_name=receiver_first_name,
                last_name=receiver_last_name,
                email=employee_email,
                company_name=company_name,
                designation=target_role,
            )

            send_email(details['gmail_id'], details['gmail_in_app_password'], employee_email, subject, personalized_message, resume_path)
            time.sleep(0.25)
            existing_entry = apollo_emails_sent_history_collection.find_one(
                {"person_id": employee["id"], "organization_id": organization_id}
            )


            new_email_entry = {
                "subject": subject,
                "content": personalized_message,
                "target_role": target_role,
                "timestamp": datetime.now(),
            }

            if existing_entry:
                # Append the new email entry to the existing emails array
                apollo_emails_sent_history_collection.update_one(
                    {"_id": existing_entry["_id"]},
                    {"$push": {"emails": new_email_entry}}
                )
                print("Entry Exist, We have started pushing.....")
            else:
                # Create a new document if no history exists
                email_history_entry = {
                    "person_id": employee["id"],
                    "receiver_email": employee_email,
                    "company": company_name,
                    "organization_id": organization_id,
                    "emails": [new_email_entry],
                }
                apollo_emails_sent_history_collection.insert_one(email_history_entry)
            count += 1
        
        if(count == 0):
            return JsonResponse({"error": f"Unable to send Emails for {company_info['name']}", "count": count})

        else:
            return JsonResponse({"success": f"{count} Emails Sent Successfully", "count": count})
    except Exception as exc:
        traceback.print_exc()
        return JsonResponse({"error": f"{exc}"})
    



def create_subject(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            details = get_user_details(request.session.get('username'))
            username = details["username"]
            subject_content = data.get("subjectContent")
            subject_title = data.get("subjectTitle")

            entry = subject_collection.find_one({'subject_title': subject_title})
            if entry:
                return JsonResponse({"error": "Subject Title Already Exists."})
            if not subject_content or not subject_title:
                return JsonResponse({"error": "Subject content or Subject Title are required."})

            # Create and insert the document
            subject_document = {
                "username": username,
                "subject_title": subject_title,
                "subject_content": subject_content,
                "timestamp": datetime.now(),
            }
            

            subject_collection.insert_one(subject_document)

            return JsonResponse({"message": "Subject saved successfully!"})

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"})

    return JsonResponse({"error": "Invalid request method."})


def fetch_subjects(request):
    try:
        details = get_user_details(request.session.get('username'))
        username = details["username"]
        subjects = list(subject_collection.find({"username": username}, {"_id": 0, "subject_title": 1, "subject_content": 1}))
        return JsonResponse({"success": True, "subjects": subjects})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
    


def get_running_job(request):
    username = request.session.get('username')  # Replace with actual user retrieval logic
    jobs = db['jobs']
    # Find the running job for the user
    running_job = jobs.find_one({"username": username, "status": "running"}, {"_id": 0})
    if running_job:
        return JsonResponse(running_job)
    else:
        return JsonResponse({"error": "No running job found for the user."}, status=404)
    
def get_job_history(request):
    username = request.session.get('username')  # Replace with actual user retrieval logic
    jobs = db['jobs']
    # Fetch all jobs for the user, sorted by most recent first
    job_history = list(jobs.find({"username": username, "status": "completed"}, {"_id": 0}).sort("created_at", -1))

    if job_history:
        return JsonResponse({"jobs": job_history})
    else:
        return JsonResponse({"error": "No job history found for the user."}, status=404)