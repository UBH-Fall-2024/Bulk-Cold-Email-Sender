
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class ResumeSelectionForm(forms.Form):
    resume = forms.ChoiceField(choices=[], label="Select Resume")

    def __init__(self, *args, **kwargs):
        user_resumes = kwargs.pop('user_resumes')
        super().__init__(*args, **kwargs)
        self.fields['resume'].choices = [(res, res) for res in user_resumes]

class TemplateSelectionForm(forms.Form):
    template_type = forms.ChoiceField(choices=[('first', 'First Email'), ('followup', 'Follow-Up Email')], label="Email Type")
    template_choice = forms.ChoiceField(choices=[], required=False, label="Select Template")
    use_gemini = forms.BooleanField(required=False, label="Generate with Gemini")

    def __init__(self, *args, **kwargs):
        templates = kwargs.pop('templates')
        super().__init__(*args, **kwargs)
        self.fields['template_choice'].choices = [(tpl, tpl) for tpl in templates]
        self.fields['template_choice'].widget.attrs['disabled'] = True  # Disable until needed

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    linkedin_url = forms.URLField(max_length=200, required=True)

    email = forms.EmailField(max_length=100, required=True)  # New Email field
    graduated_or_not = forms.ChoiceField(
        choices=[('yes', 'Yes'), ('no', 'No')],
        required=True
    )  # New Graduated field
    college = forms.CharField(max_length=200, required=False)  # New College field (optional)
    degree_name = forms.CharField(max_length=200, required=False)
    gmail_id = forms.CharField(max_length=200, required=True)
    gmail_in_app_password = forms.CharField(max_length=50, required=True)
    gemini_api_key = forms.CharField(max_length=200, required=True)
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'phone_number', 'linkedin_url', 'email', 'graduated_or_not', 'college', 'degree_name', 'password1', 'password2', 'gmail_id', 'gmail_in_app_password', 'gemini_api_key']

    def clean(self):
        cleaned_data = super().clean()
        graduated = cleaned_data.get('graduated_or_not')
        college = cleaned_data.get('college')

        # If graduated is 'yes', ensure that college is provided
        if graduated == 'yes' and not college:
            self.add_error('college', 'This field is required when you select "Yes" for graduation.')

        return cleaned_data
