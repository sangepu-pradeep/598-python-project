from django.shortcuts import render, redirect  # Importing necessary functions
from django.urls import reverse_lazy  # Importing reverse_lazy function

from friends.models import Friend  # Importing Friend model
from newsfeed.models import Post  # Importing Post model


def home(request):
    # Redirect to login if user is not authenticated
    if not request.user.is_authenticated:
        return redirect(reverse_lazy('accounts:login'))

    # Fetching user's friends
    friends = Friend.objects.friends(request.user)

    # Fetching posts with related comments and user profiles, ordered by creation time
    posts = Post.objects.prefetch_related('comments').select_related('user__profile').order_by('-created_at')

    # Rendering home page with posts and friends
    return render(request, 'home.html', {'posts': posts, 'friends': friends})
