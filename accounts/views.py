# Importing necessary modules and functions from Django
from django.contrib import messages, auth  # Importing message system and authentication module
from django.http import HttpResponseRedirect  # Importing HTTP redirection response

from django.shortcuts import render, redirect  # Importing rendering and redirection functions
from django.urls import reverse_lazy  # Importing reverse_lazy for URL redirection
from django.views.generic import CreateView, FormView, RedirectView  # Importing generic views
from .forms import *  # Importing forms from the local application

# Creating a view for user registration using CreateView
class RegisterView(CreateView):
    model = User  # Specifying the model for the view
    form_class = UserRegistrationForm  # Specifying the form class for user registration
    template_name = 'accounts/register.html'  # Specifying the template for rendering
    success_url = '/'  # Setting the URL to redirect after successful registration

    # Extra context data for the template
    extra_context = {
        'title': 'Register'
    }

    # Handling request dispatch and redirecting authenticated users
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(self.get_success_url())
        return super().dispatch(self.request, *args, **kwargs)

    # Method to define the success URL
    def get_success_url(self):
        return self.success_url

    # Handling post request for user registration
    def post(self, request, *args, **kwargs):
        # Checking if the email already exists in the database
        if User.objects.filter(email=request.POST['email']).exists():
            messages.warning(request, 'This email is already taken')
            return redirect('accounts:register')  # Redirecting if email already exists

        user_form = UserRegistrationForm(data=request.POST)  # Creating form instance with POST data

        if user_form.is_valid():  # Checking form validity
            user = user_form.save(commit=False)  # Saving user data without committing to the database
            password = user_form.cleaned_data.get("password1")  # Getting cleaned password data
            user.set_password(password)  # Setting password for the user
            user.save()  # Saving the user object to the database
            messages.success(request, 'Successfully registered')  # Displaying success message
            return redirect('accounts:login')  # Redirecting to login page after successful registration
        else:
            print(user_form.errors)  # Printing form errors for debugging purposes
            return render(request, 'accounts/register.html', {'form': user_form})  # Rendering registration form again

# Creating a view for user login using FormView
class LoginView(FormView):
    success_url = '/'  # Setting the URL to redirect after successful login
    form_class = UserLoginForm  # Specifying the form class for user login
    template_name = 'accounts/login.html'  # Specifying the template for rendering

    # Extra context data for the template
    extra_context = {
        'title': 'Login'
    }

    # Handling request dispatch and redirecting authenticated users
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(self.get_success_url())
        return super().dispatch(self.request, *args, **kwargs)

    # Method to retrieve the form class
    def get_form_class(self):
        return self.form_class

    # Handling valid form submission for user login
    def form_valid(self, form):
        auth.login(self.request, form.get_user())  # Authenticating the user
        return HttpResponseRedirect(self.get_success_url())  # Redirecting after successful login

    # Handling invalid form submission for user login
    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))  # Rendering the login form again

# Creating a view for user logout using RedirectView
class LogoutView(RedirectView):
    """
    Provides users the ability to logout
    """
    url = reverse_lazy('core:home')  # Setting the URL to redirect after logout

    # Handling GET request for user logout
    def get(self, request, *args, **kwargs):
        auth.logout(request)  # Logging out the user
        messages.success(request, 'You are now logged out')  # Displaying logout success message
        return super(LogoutView, self).get(request, *args, **kwargs)  # Redirecting after logout


# Creating a view for user logout using RedirectView
class AboutView(RedirectView):
    url = reverse_lazy('core:home')  # Setting the URL to redirect after logout

    # Handling GET request for user logout
    def get(self, request, *args, **kwargs):
        return render(request, 'accounts/about.html', {})  # Redirecting after logout
