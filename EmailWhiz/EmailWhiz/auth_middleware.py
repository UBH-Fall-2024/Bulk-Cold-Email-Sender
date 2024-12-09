from django.shortcuts import redirect
from django.urls import reverse

class AuthenticationMiddleware:
    """
    Middleware to check user authentication.
    Allows access to login and register views without authentication.
    Restricts access to other views if the user is not logged in.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed_paths = [reverse('login'), reverse('register')]  # Login and Register views
        user_logged_in = request.session.get('username')  # Check if username exists in session

        # If the user is not logged in and tries to access a restricted page
        if not user_logged_in and request.path not in allowed_paths:
            return redirect('login')  # Redirect to login page

        # If the user is logged in and accesses login/register, redirect to dashboard
        if user_logged_in and request.path in allowed_paths:
            return redirect('dashboard')  # Redirect logged-in users to the dashboard

        response = self.get_response(request)
        return response
