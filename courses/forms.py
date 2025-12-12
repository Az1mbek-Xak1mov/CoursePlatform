"""
Django forms for course creation and management.
"""
from django import forms
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from .models import Course, CourseModule, Lesson, HomeworkAssignment, Category
from decimal import Decimal


class CourseForm(forms.ModelForm):
    """Form for creating and editing courses."""
    
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.filter(parent=None),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Select one or more categories"
    )
    
    class Meta:
        model = Course
        fields = [
            'title', 'short_description', 'description',
            'categories', 'thumbnail', 'trailer_url',
            'price', 'level', 'language',
            'requirements', 'what_you_will_learn'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter course title',
                'required': True
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Brief course summary (max 500 characters)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 6,
                'placeholder': 'Detailed course description',
                'required': True
            }),
            'trailer_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://vimeo.com/...'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0',
                'step': '1000',
                'required': True
            }),
            'level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'language': forms.Select(attrs={
                'class': 'form-select'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'What students need to know beforehand'
            }),
            'what_you_will_learn': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Key learning outcomes'
            }),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title:
            # Check for duplicate slugs
            slug = slugify(title)
            existing = Course.objects.filter(slug=slug)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError("A course with this title already exists. Please choose a different title.")
        return title
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None:
            raise forms.ValidationError("Price is required.")
        if price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price


class CourseModuleForm(forms.ModelForm):
    """Form for adding/editing course modules."""
    
    class Meta:
        model = CourseModule
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Module title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Module description (optional)'
            }),
        }


class LessonForm(forms.ModelForm):
    """Form for adding/editing lessons."""
    
    class Meta:
        model = Lesson
        fields = [
            'title', 'description', 'video_url', 'video_file',
            'duration_minutes', 'text_content',
            'attachments', 'is_preview'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Lesson title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Lesson description'
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://youtube.com/... or https://vimeo.com/...'
            }),
            'video_file': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'video/mp4,video/webm,video/ogg'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1',
                'placeholder': 'Duration in minutes'
            }),
            'text_content': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 5,
                'placeholder': 'Additional text materials (optional)'
            }),
            'is_preview': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        video_url = cleaned_data.get('video_url')
        video_file = cleaned_data.get('video_file')
        
        # At least one video source should be provided (or can be empty for text-only lessons)
        # No validation needed - both can be optional
        
        return cleaned_data


class HomeworkAssignmentForm(forms.ModelForm):
    """Form for adding homework to lessons."""
    
    class Meta:
        model = HomeworkAssignment
        fields = ['title', 'description', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Assignment title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Assignment instructions'
            }),
        }
