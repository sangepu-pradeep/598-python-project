# Import necessary modules and classes
import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

# Import constants and models from the project
from core.contants.common import COMMENT_VERB
from friends.models import CustomNotification
from friends.serializers import NotificationSerializer
from .forms import PostCreateForm
from .models import *

# Define a class-based view for creating a post
class PostCreateView(CreateView):
    model = Post
    http_method_names = ['post']
    form_class = PostCreateForm
    template_name = 'home.html'
    success_url = reverse_lazy('core:home')

    # If the form is valid, set the user for the post
    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
        return super(PostCreateView, self).form_valid(form)

    # If the form is invalid, redirect to the home page
    def form_invalid(self, form):
        print(form.errors)
        return redirect(reverse_lazy('core:home'))

    # Handle the HTTP POST request
    def post(self, *args, **kwargs):
        form = self.get_form()
        self.object = None
        # If form is valid, call form_valid, else call form_invalid
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

# Define a function to create a comment
def create_comment(request, post_id=None):
    if request.method == "POST":
        # Retrieve the post object based on the provided post_id
        post = Post.objects.get(id=post_id)
        # Create a notification for the post owner about the comment
        notification = CustomNotification.objects.create(recipient=post.user, actor=request.user, verb=COMMENT_VERB,
                                                         description="commented on your post")
        # Use Channels to send a notification to the post owner
        channel_layer = get_channel_layer()
        channel = "comment_like_notifications_{}".format(post.user.username)
        async_to_sync(channel_layer.group_send)(
            channel, {
                "type": "notify",
                "command": "new_like_comment_notification",
                "notification": json.dumps(NotificationSerializer(notification).data),
                'unread_notifications': CustomNotification.objects.user_unread_notification_count(request.user)
            }
        )
        # Redirect to the home page after creating the comment
        return redirect(reverse_lazy('core:home'))
    else:
        # If the method is not POST, redirect to the home page
        return redirect(reverse_lazy('core:home'))
