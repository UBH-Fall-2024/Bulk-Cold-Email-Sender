from django.urls import path
from . import views

urlpatterns = [

    path('add_resume/', views.add_resume, name='add_resume'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home, name='home'),
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    
    path('register/', views.register_view, name='register'),
    path('view_user_details/', views.view_user_details, name='view_user_details'),
    path('list-resumes/', views.list_resumes, name='list_resumes'),
    path('suggestions-view/', views.suggestions_view, name='suggestions_view'),
    path('email-generator/', views.email_generator, name='email_generator'),
    path('templates/create', views.create_template, name='create_template'),
    path('templates/list', views.list_templates, name='list_templates'),
    path('select-email-template/', views.select_email_template, name='select_email_template'),
    path('upload-excel/', views.upload_excel, name='upload_excel'),
    path('preview-template/', views.preview_template, name='preview_template'),
    path('create-subject/', views.create_subject, name='create_subject'),
    
    path('email_history/', views.email_history, name='email_history'),
    path('add_employer_details/', views.add_employer_details, name='add_employer_details'),
    path('update-apollo-apis/', views.update_apollo_apis, name='update_apollo_apis'),
    path('create-companies-data/', views.create_companies_data, name='create_companies_data'),
    path('scrape-employees-data/select-companies-dataset', views.get_companies_datasets, name='get_companies_datasets'),
    path('scrape-employees-data/select-companies', views.select_companies, name='select_companies'),
    
    path('scrape-employees-data/fetch-employees', views.fetch_employees_data, name='fetch_employees_data'),
    path('scrape-employees-data/unlock-employees-emails', views.unlock_emails, name='unlock_emails'),
    path('apollo/send-cold-emails', views.send_cold_emails_through_apollo_emails, name='send_cold_emails_through_apollo_emails'),
     path('apollo/jobs', views.view_jobs, name='view_jobs'),
    
]

