from django.urls import path
from . import views

urlpatterns = [

    path('save_resume/', views.save_resume, name='save_resume'),
    path('send-emails/', views.send_emails, name='send_emails'),
    path('email-generator_post/', views.email_generator_post, name='email_generator_post'),
    path('templates/create/', views.create_template_post, name='create_template_post'),
    path('templates/list/', views.create_template_post, name='list_templates'),
    path('generate_followup/', views.generate_followup, name='generate_followup'),
    path('send_followup/', views.send_followup, name='send_followup'),
    path('update-apollo-apis/<str:api_name>/', views.update_apollo_apis, name='update_apollo_apis'),
    path('hit-apollo-api/<str:api_name>/', views.hit_apollo_api, name='hit_apollo_api'),
    # path('get-companies-id/', views.get_companies_id, name='get_companies_id'),
    path('add-keyword/', views.add_keyword, name='add_keyword'),
    path('keyword-counts/', views.get_keyword_combinations_counts, name='get_keyword_combinations_counts'),
    path('get-companies/', views.scrape_companies, name='scrape_companies'),
    path('company-count/', views.company_count, name='company_count'),
    path('apollo-emails-count/', views.apollo_emails_count, name='apollo_emails_count'),
    path('create-subject/',  views.create_subject, name='create_subject'),
    path('fetch-subjects/',  views.fetch_subjects, name='fetch_subjects'),
    
    path('get-non-processed-companies/', views.get_non_processed_companies, name='get_non_processed_companies'),
    path('search-companies/', views.search_companies, name='search_companies'),
    path('fetch-employees/', views.fetch_employees, name='fetch_employees'),
    path('fetch-employees-emails/', views.fetch_employees_emails, name='fetch_employees_emails'),
    path('emails-sent-count/', views.emails_sent_count, name='emails_sent_count'),
    
    path('employees-count/', views.employees_count, name='employees_count'),
    
    path('apollo/send-cold-emails-by-automation/', views.send_cold_emails_by_automation_through_apollo_emails, name='send_cold_emails_by_automation_through_apollo_emails'),
    path('apollo/send-cold-emails-by-company/', views.send_cold_emails_by_company_through_apollo_emails, name='send_cold_emails_by_company_through_apollo_emails')
]

