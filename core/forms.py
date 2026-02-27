from django import forms
from django.contrib.auth.models import User
from .models import ForumPost, ForumAnswer, SuccessStory


class ForumPostForm(forms.ModelForm):
    """Form for creating forum posts."""
    class Meta:
        model = ForumPost
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Enter post title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'rows': 8,
                'placeholder': 'Write your post here...'
            }),
        }


class ForumAnswerForm(forms.ModelForm):
    """Form for creating forum answers."""
    class Meta:
        model = ForumAnswer
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'rows': 4,
                'placeholder': 'Write your answer...'
            }),
        }


class SuccessStoryForm(forms.ModelForm):
    """Form for submitting success stories."""
    class Meta:
        model = SuccessStory
        fields = ['company_name', 'contact_name', 'contact_email', 'logo', 'story']
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Your company name'
            }),
            'contact_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Your name'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'your.email@example.com'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'accept': 'image/*'
            }),
            'story': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'rows': 10,
                'placeholder': 'Tell us your success story...'
            }),
        }

