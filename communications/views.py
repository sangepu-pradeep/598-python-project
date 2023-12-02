import json  # Importing JSON module for JSON handling

from django.contrib.auth.decorators import login_required  # Decorator for login requirement
from django.shortcuts import render, redirect  # Functions for rendering and redirection
from django.urls import reverse_lazy  # Utility for reversing URLs
from django.utils.safestring import mark_safe  # Utility for marking strings as safe

from accounts.models import User  # Importing the User model from accounts
from friends.models import Friend  # Importing the Friend model

# View to display all messages
@login_required(login_url=reverse_lazy("accounts:login"))  # Requires login; redirects to login if not logged in
def all_messages(request):
    friends = Friend.objects.friends(request.user)  # Fetching user's friends
    return render(request, "communications/all-messages.html", {'friends': friends})  # Rendering the messages template

# View for displaying conversation with a single friend
@login_required(login_url=reverse_lazy("accounts:login"))  # Requires login; redirects to login if not logged in
def messages_with_one_friend(request, friend):
    if request.user.username == friend:  # If user tries to view their own messages, redirect to all-messages
        return redirect(reverse_lazy('communications:all-messages'))

    try:
        if not User.objects.get(username=friend):  # If friend user doesn't exist, redirect to all-messages
            return redirect(reverse_lazy('communications:all-messages'))
    except:
        return redirect(reverse_lazy('communications:all-messages'))  # Redirect if any exception occurs

    friend_user = User.objects.get(username=friend)  # Getting the friend's user object

    # If the requested user and friend are not friends, redirect to all-messages
    if not Friend.objects.are_friends(request.user, friend_user):
        return redirect(reverse_lazy('communications:all-messages'))

    friends = Friend.objects.friends(request.user)  # Fetching user's friends
    return render(request, "communications/friend-messages.html", {
        'friends': friends,
        'friend_user': friend_user,
        'friend_name_json': mark_safe(json.dumps(friend)),  # Passing friend's name as JSON string
        'username': mark_safe(json.dumps(request.user.username)),  # Passing user's username as JSON string
    })
