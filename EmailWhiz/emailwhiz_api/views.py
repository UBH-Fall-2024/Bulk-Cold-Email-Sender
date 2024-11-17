
import copy
from django.shortcuts import render
from django.http import HttpResponse
from PyPDF2 import PdfReader
from django.conf import settings
from django.shortcuts import render, redirect

from emailwhiz_api.email_sender import send_email
from .forms import ResumeSelectionForm, TemplateSelectionForm
import os

import pytz

from datetime import datetime

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

CustomUser = get_user_model()

from dotenv import load_dotenv
load_dotenv()

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


        print("LL: ", details)
        username = details['username']
        selected_resume = request.POST.get('resume')
        selected_template = request.POST.get('template')
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
        print(rows)
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
            data.append(emp_data)

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
            subject = f"[{name}]: Exploring {designation} Roles at {company_name}"
        
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
        
