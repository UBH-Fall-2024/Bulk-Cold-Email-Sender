
# EmailWhiz/emailwhiz_ui/views.py
from django.shortcuts import redirect, render
from django.conf import settings
import os
from PyPDF2 import PdfReader
import requests
import os
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.contrib.auth.models import User

from emailwhiz_api.views import get_user_details
from emailwhiz_ui.forms import CustomUserCreationForm


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
import json
from emailwhiz_ui.forms import CustomUserCreationForm
from pymongo import MongoClient

client = MongoClient('mongodb+srv://shoaibthakur23:Shoaib%40345@cluster0.xjugu.mongodb.net/')  # Replace with your MongoDB connection URI
db = client['EmailWhiz']

apollo_apis_curl_collection = db['apollo_apis_curl']
def suggestions_view(request):
    suggestions = [
        {"first_name": "Alice", "last_name": "Johnson", "organization_email_id": "alice.johnson@aws.com", "organization": "Amazon"},
        {"first_name": "Bob", "last_name": "Smith", "organization_email_id": "bob.smith@aws.com", "organization": "Amazon"},
        {"first_name": "Carol", "last_name": "Davis", "organization_email_id": "carol.davis@aws.com", "organization": "Amazon"},
        {"first_name": "David", "last_name": "Wilson", "organization_email_id": "david.wilson@aws.com", "organization": "Amazon"},
        {"first_name": "Eve", "last_name": "Miller", "organization_email_id": "eve.miller@aws.com", "organization": "Amazon"}
    ]
    
    return render(request, 'suggestions.html', {'suggestions': suggestions})

def add_employer_details(request):
    resume = request.GET.get('resume')
    
    if not resume:
        # If the parameter is missing, return a 400 Bad Request response
        return HttpResponseBadRequest('Missing required query parameter: param1')

    body = {"resume": resume}
    return render(request, 'email_generator.html', body)


def view_generated_emails(request, data):
    # body = json.loads(request.body)
    # print(data)
    body = {
        "data": [{
            "first_name": "firstName",
            "last_name": "lastName",
            "email": "email",
            "company": "company",
            "job_role": "jobRole",
            "email_content": "email_content"
        },
        ]
    }
    return render(request, 'view_generated_emails.html', body)

def view_user_details(request):
    details = get_user_details(request.user)
    print("Details: ", details)
    if details['graduation_done'] == True:
        details['graduation_done'] = 'Yes'
    else:
        details['graduation_done'] = 'No'
    resumes_dir = os.path.join(settings.BASE_DIR, 'emailwhiz_api', 'users', details['username'], 'resumes')
    print("resume_dir: ", resumes_dir, settings.BASE_DIR)
    resumes = [f for f in os.listdir(resumes_dir) if f.endswith('.pdf')]
    print("resumes: ", resumes)
    return render(request, 'view_user_details.html', {'details': details,  'username': details['username'],  'resumes': resumes})

def home(request):
    details = get_user_details(request.user)
    upload_dir = os.path.join(settings.MEDIA_ROOT, f'{details["username"]}/resumes')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    return render(request, 'base.html')

def list_resumes(request):
    details = get_user_details(request.user)

    selected_template = request.POST.get('selected_template')
    
    username = details['username']  # Placeholder: Replace with the actual user's email
    print("username:", username)
    resumes_dir = os.path.join(settings.BASE_DIR, 'emailwhiz_api', 'users', username, 'resumes')
    print("resume_dir: ", resumes_dir, settings.BASE_DIR)
    resumes = [f for f in os.listdir(resumes_dir) if f.endswith('.pdf')]
    print("resumes: ", resumes)
    return render(request, 'list_resumes.html', {'resumes': resumes, 'username': username, 'selected_template': selected_template})

def select_email_template(request):
    # Get the user's username and templates directory
    details = get_user_details(request.user)
    username = details['username']
    templates_dir = os.path.join(settings.BASE_DIR, 'emailwhiz_api', 'users', username, 'templates')
    
    # Load template names and their content
    templates = []
    if os.path.exists(templates_dir):
        for template_file in os.listdir(templates_dir):
            if template_file.endswith('.txt'):
                template_path = os.path.join(templates_dir, template_file)
                with open(template_path, 'r') as f:
                    content = f.read()
                templates.append({
                    'name': template_file, 
                    'content': content
                })

    return render(request, 'select_template.html', {'templates': templates})

def list_templates(request):
    details = get_user_details(request.user)
    username = details['username']
    templates_dir = os.path.join(settings.BASE_DIR, 'emailwhiz_api', 'users', username, 'templates')
    # Initialize list to hold template details
    templates = []

    # Loop through each file in the directory
    for template_file in os.listdir(templates_dir):
        if template_file.endswith('.txt'):
            template_path = os.path.join(templates_dir, template_file)
            with open(template_path, 'r') as file:
                content = file.read()
            
            # Append dictionary with filename and content
            templates.append({
                'name': template_file[:-4],  # Removing '.txt' from display name
                'content': content
            })

    # Render the list_templates.html with template details
    return render(request, 'list_templates.html', {'templates': templates, 'username': username})
    

def create_template(request):
    return render(request, 'create_template.html')



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

def create_subject(request):
    return render(request, 'create_subject.html')

def email_generator(request):
    resume = request.POST.get('selected_resume')
    selected_template = request.POST.get('selected_template')
    print("OO: ", resume, selected_template)
    return render(request, 'email_generator.html', {"resume": resume, "template": selected_template})
    



def add_resume(request):
    return render(request, 'add_resume.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Change 'home' to the name of the view or URL where you want to redirect on successful login
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful! Please log in.")
            return redirect('login')  # Redirect to the login page after successful registration
        else:
            # Display error messages if form is not valid
            messages.error(request, "Please fix the errors below.")
            return render(request, 'register.html', {'form': form})
    else:
        form = CustomUserCreationForm()  # Instantiate an empty form for GET request
    return render(request, 'register.html', {'form': form})

def add_employer_details(request):
    # body = json.loads(request.body)
    body = {"resume": "abcd"}
    return render(request, 'email_generator.html', body)



def email_history(request):
    details = get_user_details(request.user)
    username = details['username']  # Get the logged-in user's username
    user_dir = os.path.join(settings.BASE_DIR, 'emailwhiz_api', 'users', username)
    history_file = os.path.join(user_dir, 'history.json')
    resumes_dir = os.path.join(settings.BASE_DIR, 'emailwhiz_api', 'users', username, 'resumes')
    print("resume_dir: ", resumes_dir, settings.BASE_DIR)
    resumes = [f for f in os.listdir(resumes_dir) if f.endswith('.pdf')]
    print("resumes: ", resumes)
    # Check if the history file exists
    if os.path.exists(history_file):
        with open(history_file, 'r') as file:
            history_data = json.load(file)
    else:
        history_data = {"history": []}
    
    history_by_company = {}
    for entry in history_data["history"]:
        company = entry.get('company')
        if company not in history_by_company:
            history_by_company[company] = []
        history_by_company[company].append(entry)

    # Prepare the context and pass it to the template
    context = {'history_by_company': history_by_company, 'resumes': resumes, 'username': username}
    print("history: ", history_data, history_file)
    return render(request, 'email_history.html', context)


def update_apollo_apis(request):
    # Load or initialize JSON data
    details = get_user_details(request.user)
    username = details['username']
    # print("username: ", username)
    api_details = apollo_apis_curl_collection.find_one({'username': username})

    # print("api_details: ", api_details)
    if not api_details:
        context = {
            'api1_value': api_details.get('api1', {}).get('curl_request', ''),
            'api2_value': api_details.get('api2', {}).get('curl_request', ''),
            'api3_value': api_details.get('api3', {}).get('curl_request', ''),
        }
    else:
        context = {
            'api1_value': api_details["apis"].get('api1', {}).get('curl_request', ''),
            'api2_value': api_details["apis"].get('api2', {}).get('curl_request', ''),
            'api3_value': api_details["apis"].get('api3', {}).get('curl_request', ''),
        }
    print("context: ", context)
    return render(request, 'update_apollo_apis.html', context)



def create_companies_data(request):
    return render(request, 'create_companies_data.html')


def get_companies_datasets(request):
    details = get_user_details(request.user)
    username = details['username']
    user_dir = os.path.join(settings.MEDIA_ROOT, username)
    datasets = [
        f for f in os.listdir(user_dir) if f.endswith('.json')
    ]
    print("Datasets: ", datasets)
    return render(request, 'select_companies_dataset.html', { 'datasets': datasets})

def select_companies(request):
    dataset = request.GET.get('dataset')
    if not dataset:
        return JsonResponse({'error': 'Dataset not selected'}, status=400)

    details = get_user_details(request.user)
    username = details['username']
    user_dir = os.path.join(settings.MEDIA_ROOT, username, dataset)

    with open(user_dir, 'r') as f:
        companies = json.load(f)
    return render(request, 'select_companies.html', {'companies': companies})

def select_companies(request):
    dataset = request.GET.get('dataset')
    if not dataset:
        return JsonResponse({'error': 'Dataset not selected'}, status=400)

    details = get_user_details(request.user)
    username = details['username']
    user_dir = os.path.join(settings.MEDIA_ROOT, username, dataset)

    with open(user_dir, 'r') as f:
        companies = json.load(f)
    return render(request, 'select_companies.html', {'companies': companies})

def fetch_employees_data(request):
    return render(request, 'fetch_employees.html')

def unlock_emails(request):
    return render(request, 'unlock_emails.html')

def send_cold_emails_through_apollo_emails(request):
    details = get_user_details(request.user)
    username = details['username']
    templates_dir = os.path.join(settings.BASE_DIR, 'emailwhiz_api', 'users', username, 'templates')
    
    # Load template names and their content
    templates = []
    if os.path.exists(templates_dir):
        for template_file in os.listdir(templates_dir):
            if template_file.endswith('.txt'):
                template_path = os.path.join(templates_dir, template_file)
                with open(template_path, 'r') as f:
                    content = f.read()
                templates.append({
                    'name': template_file, 
                    'content': content
                })

    details = get_user_details(request.user)

    resumes_dir = os.path.join(settings.BASE_DIR, 'emailwhiz_api', 'users', username, 'resumes')
    print("resume_dir: ", resumes_dir, settings.BASE_DIR)
    resumes = [f for f in os.listdir(resumes_dir) if f.endswith('.pdf')]
    print("resumes: ", resumes)
    return render(request, 'send_cold_emails_through_apollo_emails.html', {'templates': templates, 'resumes': resumes})