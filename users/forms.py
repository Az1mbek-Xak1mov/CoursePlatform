"""
Forms for user registration and profile management.
"""
from django import forms
from django.core.validators import RegexValidator
from .models import User


class PhoneRegistrationForm(forms.Form):
    """Step 1: Phone number input for OTP registration."""
    phone_regex = RegexValidator(
        regex=r'^\+998[0-9]{9}$',
        message="Phone number must be in format: '+998XXXXXXXXX'"
    )
    
    phone_number = forms.CharField(
        max_length=13,
        validators=[phone_regex],
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+998901234567',
            'pattern': r'\+998[0-9]{9}',
        })
    )
    
    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        if User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("This phone number is already registered.")
        return phone


class OTPVerificationForm(forms.Form):
    """Step 2: OTP verification form."""
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-input otp-input',
            'placeholder': '000000',
            'maxlength': '6',
            'pattern': r'[0-9]{6}',
            'autocomplete': 'one-time-code',
        })
    )


class UserDetailsForm(forms.Form):
    """Step 3: User details after OTP verification."""
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your first name',
        })
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your last name',
        })
    )
    age = forms.IntegerField(
        min_value=10,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your age',
            'min': '10',
            'max': '120',
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Create a password',
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm your password',
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        
        if password1 and len(password1) < 8:
            raise forms.ValidationError("Password must be at least 8 characters.")
        
        return cleaned_data


class EmailRegistrationForm(forms.Form):
    """Email-based registration form."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your email',
        })
    )
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your first name',
        })
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your last name',
        })
    )
    age = forms.IntegerField(
        min_value=10,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your age',
            'min': '10',
            'max': '120',
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Create a password',
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm your password',
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        
        if password1 and len(password1) < 8:
            raise forms.ValidationError("Password must be at least 8 characters.")
        
        return cleaned_data


class PhoneLoginForm(forms.Form):
    """Phone number login form (sends OTP)."""
    phone_regex = RegexValidator(
        regex=r'^\+998[0-9]{9}$',
        message="Phone number must be in format: '+998XXXXXXXXX'"
    )
    
    phone_number = forms.CharField(
        max_length=13,
        validators=[phone_regex],
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+998901234567',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your password',
        })
    )


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'age']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'age': forms.NumberInput(attrs={'class': 'form-input', 'min': '10', 'max': '120'}),
        }


class UserRegistrationForm(forms.Form):
    """Combined form for phone registration (Phone + Details)."""
    phone_regex = RegexValidator(
        regex=r'^\+998[0-9]{9}$',
        message="Phone number must be in format: '+998XXXXXXXXX'"
    )
    
    phone_number = forms.CharField(
        max_length=13,
        validators=[phone_regex],
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+998901234567',
            'pattern': r'\+998[0-9]{9}',
        })
    )
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your first name',
        })
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your last name',
        })
    )
    age = forms.IntegerField(
        min_value=10,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your age',
            'min': '10',
            'max': '120',
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Create a password',
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm your password',
        })
    )
    
    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        if User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("This phone number is already registered.")
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        
        if password1 and len(password1) < 8:
            raise forms.ValidationError("Password must be at least 8 characters.")
        
        return cleaned_data
