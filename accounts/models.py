# Importing necessary modules
from django.contrib.auth.models import AbstractUser  # Importing the AbstractUser class from Django
from django.db import models  # Importing the models module from Django

# Creating a custom User model that extends Django's AbstractUser
class User(AbstractUser):
    # Field for the username with specific constraints
    username = models.CharField(
        'username',
        max_length=50,
        unique=True,
        help_text='Required. 50 characters or fewer. Letters, digits and @/./+/-/_ only.',
        error_messages={
            'unique': "A user with that username already exists.",
        },
    )
    # Field for the email with uniqueness constraint and error message
    email = models.EmailField(
        unique=True,
        blank=False,
        error_messages={
            'unique': "A user with that email already exists.",
        }
    )
    # Field for gender with a maximum length of 20 characters
    gender = models.CharField(max_length=20)
    # Field for status, a boolean field with default value as False
    status = models.BooleanField(default=False)
    # Field for an optional 'about' section, a text field allowing blank values
    about = models.TextField(blank=True)

    # Setting the field 'email' as the USERNAME_FIELD for authentication
    USERNAME_FIELD = "email"
    # Fields required during user creation along with the USERNAME_FIELD
    REQUIRED_FIELDS = ["username", "gender"]

    # Method to return a string representation of the object for Python 2
    def __unicode__(self):
        return self.email

    # Method to return a string representation of the object for Python 3
    def __str__(self):
        return self.get_full_name()  # Returning the full name of the user
