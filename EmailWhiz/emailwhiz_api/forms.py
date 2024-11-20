# forms.py
from django import forms

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
