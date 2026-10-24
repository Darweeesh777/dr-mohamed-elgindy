import re

from django import forms

from .content import get_content
from .models import ConsultationRequest

PHONE_ALLOWED = re.compile(r'^\+?[\d\s\-()]+$')


class ConsultationForm(forms.ModelForm):
    # Honeypot: hidden from people, often filled in by spam bots.
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'tabindex': '-1', 'autocomplete': 'off',
    }))

    class Meta:
        model = ConsultationRequest
        fields = ['request_type', 'full_name', 'phone', 'email', 'preferred_contact', 'matter', 'message', 'consent']
        widgets = {
            'request_type': forms.RadioSelect,
            'preferred_contact': forms.RadioSelect,
            'message': forms.Textarea(attrs={'rows': 4, 'maxlength': 1000}),
        }

    def __init__(self, *args, lang='ar', **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        t = get_content(lang)['form']
        self.text = t

        f = self.fields
        f['request_type'].label = t['request_type']
        f['request_type'].choices = list(t['request_types'].items())
        f['full_name'].label = t['full_name']
        f['full_name'].widget.attrs.update({'autocomplete': 'name'})
        f['phone'].label = t['phone']
        f['phone'].help_text = t['phone_help']
        f['phone'].widget.input_type = 'tel'
        f['phone'].widget.attrs.update({'autocomplete': 'tel', 'dir': 'ltr', 'inputmode': 'tel'})
        f['email'].label = t['email']
        f['email'].widget.attrs.update({'autocomplete': 'email', 'dir': 'ltr'})
        f['preferred_contact'].label = t['preferred_contact']
        f['preferred_contact'].choices = list(t['contacts'].items())
        f['matter'].label = t['matter']
        f['matter'].choices = list(t['matters'].items())
        f['message'].label = t['message']
        f['message'].help_text = t['message_help']
        f['consent'].label = t['consent']
        f['consent'].required = True

    def full_clean(self):
        super().full_clean()
        # Point each invalid input at its help text and error message for screen readers.
        for name in self.errors:
            if name not in self.fields:
                continue
            field_id = self[name].auto_id
            described = [f'{field_id}_error']
            if self.fields[name].help_text:
                described.append(f'{field_id}_helptext')
            self.fields[name].widget.attrs.update({
                'aria-invalid': 'true',
                'aria-describedby': ' '.join(described),
            })

    def clean_website(self):
        if self.cleaned_data.get('website'):
            raise forms.ValidationError('Invalid submission.')
        return ''

    def clean_full_name(self):
        return ' '.join(self.cleaned_data['full_name'].split())

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        digits = re.sub(r'\D', '', phone)
        if not PHONE_ALLOWED.match(phone) or not 7 <= len(digits) <= 15:
            raise forms.ValidationError(self.text['phone_invalid'])
        return phone

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('preferred_contact') == 'email' and not cleaned.get('email'):
            self.add_error('email', self.text['email_required'])
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.language = self.lang
        if commit:
            obj.save()
        return obj
