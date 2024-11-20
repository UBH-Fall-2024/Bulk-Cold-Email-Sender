[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/_U2QbDVP)


Readme:
Setup:
1. You should have Enabled 2FA in our Gmail Account.
2. You need to create Sign-in Password. (https://myaccount.google.com/apppasswords)
3. Add 3 Environment Variables or edit in .env file:
EMAIL_USERNAME=abc@gmail.com
EMAIL_PASSWORD='sign-in-app-password'
API_KEY='abcd'
4. API_KEY represents Gemini API Key

Don't remove '' in the EMAIL_PASSWORD & API_KEY field.

Instructions:
1. Make sure you have all dependencies install.
- Setup python 3.12
- Create virtual environment: python3 -m venv .venv
- Activate virtual environment: source .venv/bin/activate
- Install dependencies: pip install -r requirements.txt
2. To start the server:
- cd EmailWhiz
- python manage.py migrate
- python manage.py runserver
3. Open 127.0.0.1:8000 on your browser & enjoy.
