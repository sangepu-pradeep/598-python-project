# Import necessary modules/classes
from rest_framework.decorators import api_view
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.models import User
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import JsonResponse
from django.views.generic import ListView
from django.db.models import Q

# Import constants and serializers from the project
from core.contants.common import FRIEND_REQUEST_VERB
from .serializers import NotificationSerializer, FriendshipRequestSerializer
from .models import FriendshipRequest, Friend, CustomNotification

# Define a class-based view inheriting LoginRequiredMixin and ListView for finding friends
class FindFriendsListView(LoginRequiredMixin, ListView):
    model = Friend
    context_object_name = 'users'
    template_name = "friends/find-friends.html"

    # Retrieve users who are not friends and have not received/sent a friend request
    def get_queryset(self):
        current_user_friends = self.request.user.friends.values('id')
        sent_request = list(
            FriendshipRequest.objects.filter(Q(from_user=self.request.user))
            .exclude(to_user_id=self.request.user.id)
            .values_list('to_user_id', flat=True))
        users = User.objects.exclude(id__in=current_user_friends).exclude(id__in=sent_request).exclude(
            id=self.request.user.id)
        return users

# Define a class-based view inheriting LoginRequiredMixin and ListView for friend requests
class FriendRequestsListView(LoginRequiredMixin, ListView):
    """
    Get all friend requests current user got
    """
    model = Friend
    context_object_name = 'friend_requests'
    template_name = "friends/friend-requests.html"

    # Retrieve friend requests received by the current user
    def get_queryset(self):
        return Friend.objects.got_friend_requests(user=self.request.user)

# Define a function to send a friend request
def send_request(request, username=None):
    # Check if the username exists, if yes, send a friend request
    if username is not None:
        friend_user = User.objects.get(username=username)
        try:
            friend_request = Friend.objects.add_friend(request.user, friend_user, message='Hi! I would like to add you')
        except Exception as e:
            # If an error occurs during the request, return an error response
            data = {
                'status': False,
                'message': str(e),
            }
            return JsonResponse(data)
        # Use Channels to notify the friend about the new friend request
        channel_layer = get_channel_layer()
        channel = "all_friend_requests_{}".format(friend_user.username)
        async_to_sync(channel_layer.group_send)(
            channel, {
                "type": "notify",  # method name
                "command": "new_friend_request",
                "notification": FriendshipRequestSerializer(friend_request).data
            }
        )
        # Return a success response after sending the request
        data = {
            'status': True,
            'message': "Request sent.",
        }
        return JsonResponse(data)
    else:
        pass

# Define a function to accept a friend request
def accept_request(request, friend=None):
    # Check if the friend username exists, if yes, accept the friend request
    if friend is not None:
        friend_user = User.objects.get(username=friend)
        friend_request = FriendshipRequest.objects.get(to_user=request.user, from_user=friend_user)
        friend_request.accept()
        # Return a success response after accepting the request
        data = {
            'status': True,
            'message': "You accepted friend request",
        }
        return JsonResponse(data)

# Define an API view to cancel a friend request
@api_view(['DELETE'])
def cancel_request(request, friend=None):
    # Check if the friend username exists, if yes, cancel the friend request
    if friend is not None:
        friend_user = User.objects.get(username=friend)
        friend_request = FriendshipRequest.objects.get(to_user=request.user, from_user=friend_user)
        friend_request.cancel()
        # Return a success response after canceling the request
        data = {
            'status': True,
            'message': "Your friend request is removed",
        }
        return JsonResponse(data)
