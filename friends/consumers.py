import json  # Importing JSON module
from channels.db import database_sync_to_async  # Importing database related functions
from channels.generic.websocket import AsyncJsonWebsocketConsumer  # Websocket consumer
from django.contrib.auth import get_user_model  # Function to get User model
from django.contrib.auth.models import AnonymousUser  # Anonymous user model
from django.core import serializers  # Serializer for queryset serialization

from .models import CustomNotification, Friend  # Importing custom models
from .serializers import NotificationSerializer, FriendshipRequestSerializer  # Importing serializers

User = get_user_model()  # Getting User model dynamically

class FriendRequestConsumer(AsyncJsonWebsocketConsumer):
    # Function to fetch friend requests asynchronously from the database
    @database_sync_to_async
    def fetch_friend_requests(self):
        user = self.scope['user']

        # Getting friend requests for the user
        friend_requests = Friend.objects.got_friend_requests(user=user)
        serializer = FriendshipRequestSerializer(friend_requests, many=True)  # Serializing friend requests
        content = {
            'type': 'all_friend_requests',
            'command': 'all_friend_requests',
            'friend_requests': serializer.data
        }
        return content

    # Function to send all friend requests to the user
    async def send_all_friend_requests(self):
        user = self.scope['user']
        if user.is_anonymous:
            return {'type': 'anonymous_user', 'command': 'all_friend_requests', 'friend_requests': []}

        content = await self.fetch_friend_requests()  # Fetching friend requests
        channel = "all_friend_requests_{}".format(user.username)  # Creating channel for friend requests
        await self.channel_layer.group_send(channel, content)  # Sending friend requests to the channel

    # Function to convert notifications to JSON format
    def notifications_to_json(self, notifications):
        result = []
        for notification in notifications:
            result.append(self.notification_to_json(notification))
        return result

    # Function to convert a single notification to JSON format
    @staticmethod
    def notification_to_json(notification):
        return {
            'actor': serializers.serialize('json', [notification.actor]),
            'recipient': serializers.serialize('json', [notification.recipient]),
            'verb': notification.verb,
            'created_at': str(notification.timestamp)
        }

    # Function called when a WebSocket connection is established
    async def connect(self):
        user = self.scope['user']
        grp = 'all_friend_requests_{}'.format(user.username)  # Group name for friend requests
        await self.accept()  # Accepting the WebSocket connection
        await self.channel_layer.group_add(grp, self.channel_name)  # Adding to the group
        await self.send_all_friend_requests()  # Sending all friend requests to the user

    # Function called when a WebSocket connection is closed
    async def disconnect(self, close_code):
        user = self.scope['user']
        grp = 'all_friend_requests_{}'.format(user.username)  # Group name for friend requests
        await self.channel_layer.group_discard(grp, self.channel_name)  # Removing from the group

    # Function to handle receiving all friend requests
    async def all_friend_requests(self, event):
        await self.send_json(event)  # Sending all friend requests in JSON format

    # Function to handle sending notifications
    async def notify(self, event):
        await self.send_json(event)  # Sending notifications in JSON format

    # Function to handle anonymous user event
    async def anonymous_user(self, event):
        await self.send_json(event)  # Sending an anonymous user event

    # Function to handle receiving data over WebSocket
    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        data = json.loads(text_data)
        # if data['command'] == 'fetch_friend_requests':
        #     await self.fetch_friend_requests()  # Unused conditional block
