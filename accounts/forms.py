from django import forms  # Importing the forms module from Django
from django.contrib.auth import authenticate  # Importing the authenticate function for user authentication
from django.contrib.auth.forms import UserCreationForm, UsernameField  # Importing forms related to user creation/authentication
from .models import User  # Importing the User model from the local application

# Creating a form for user registration, inheriting from UserCreationForm
class UserRegistrationForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Updating widget attributes to set placeholders for username, email, and passwords
        self.fields['username'].widget.attrs.update({'placeholder': 'Enter Username'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Enter Email'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Enter password'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Repeat your password'})
        # Commented out line updating the placeholder for email field based on label or default email

    class Meta:
        model = User  # Setting the model for this form to the User model
        # Defining the fields to be displayed in the form for user registration
        fields = (
            "username",
            "email",
            "gender",
            "password1",
            "password2"
        )
        # Commented out section defining widgets for password fields

    # Validation for ensuring the username does not contain spaces
    def clean_username(self):
        username = self.cleaned_data['username']
        print(username)  # Printing the username (possibly for debugging)
        if ' ' in username:  # Checking for spaces in the username
            raise forms.ValidationError("Username can't contain spaces.")
        return username

    # Custom save method for the UserCreationForm
    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

# Creating a form for user login
class UserLoginForm(forms.Form):
    email = forms.EmailField(label="Email")  # Creating an email field in the login form
    password = forms.CharField(  # Creating a password field in the login form
        label="Password",
        strip=False,
        widget=forms.PasswordInput,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        # Updating widget attributes to set placeholders for email and password fields
        self.fields['email'].widget.attrs.update({'placeholder': 'Enter Email'})
        self.fields['password'].widget.attrs.update({'placeholder': 'Enter Password'})

    # Validation to authenticate the user based on provided email and password
    def clean(self, *args, **kwargs):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            self.user = authenticate(email=email, password=password)

            if self.user is None:
                raise forms.ValidationError("User Does Not Exist.")
            if not self.user.check_password(password):
                raise forms.ValidationError("Password Does not Match.")
            if not self.user.is_active:
                raise forms.ValidationError("User is not Active.")

        # Commented out return statement that calls the parent clean method
        # return self.cleaned_data
        return super(UserLoginForm, self).clean(*args, **kwargs)

    # Method to retrieve the authenticated user
    def get_user(self):
        return self.user
