
# from django.contrib.auth.models import AbstractUser
# from django.db import models

# class CustomMongoDBUser(AbstractUser):
#     phone_number = models.CharField(max_length=15, null=True, blank=True)
#     linkedin_url = models.URLField(max_length=200, null=True, blank=True)
#     graduated_or_not = models.CharField(max_length=10, choices=[('yes', 'Yes'), ('no', 'No')], default='no')
#     college = models.CharField(max_length=255, null=True, blank=True)
#     degree_name = models.CharField(max_length=255, null=True, blank=True)
#     gmail_id = models.EmailField(null=True, blank=True)
#     gmail_in_app_password = models.CharField(max_length=255, null=True, blank=True)
#     gemini_api_key = models.CharField(max_length=255, null=True, blank=True)

# # Update AUTH_USER_MODEL in settings.py
# AUTH_USER_MODEL = 'emailwhiz_api.CustomMongoDBUser'
# # Create your models here.
