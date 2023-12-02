# Import necessary modules and functions
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core import serializers

# Import models and serializers
from friends.models import CustomNotification
from friends.serializers import NotificationSerializer

# Get the User model
User = get_user_model()

# Define a function to fetch data asynchronously from the database
@database_sync_to_async
def get_data(user):
    return CustomNotification.objects.select_related('actor').filter(recipient=user, type="comment", unread=True)[:7]

# Define a WebSocket consumer class to handle notifications
class NotificationConsumer(AsyncJsonWebsocketConsumer):

    # Function to fetch notifications asynchronously from the database
    @database_sync_to_async
    def fetch_notifications(self):
        user = self.scope['user']
        # Check if the user is anonymous
        if user.is_anonymous:
            return {'type': 'anonymous_user'}  # Return message for anonymous user
        # Fetch notifications for authenticated users
        notifications = CustomNotification.objects.select_related('actor').filter(recipient=user, verb="comment",
                                                                                  is_read=False)[:4]
        serializer = NotificationSerializer(notifications, many=True)
        # Prepare data to send through WebSocket
        content = {
            'type': 'all_notifications',
            'command': 'notifications',
            'notifications': serializer.data,
            'unread_notifications': CustomNotification.objects.user_unread_notification_count(user)
        }
        return content

    # Function to send all notifications to the user
    async def send_all_notifications(self):
        user = self.scope['user']
        content = await self.fetch_notifications()
        channel = "comment_like_notifications_{}".format(user.username)
        await self.channel_layer.group_send(channel, content)

    # Connection established for WebSocket
    async def connect(self):
        user = self.scope['user']
        grp = 'comment_like_notifications_{}'.format(user.username)
        await self.accept()  # Accept the connection
        await self.channel_layer.group_add(grp, self.channel_name)  # Add user to a specific group
        await self.send_all_notifications()  # Send all notifications to the user

    # Disconnection from WebSocket
    async def disconnect(self, close_code):
        user = self.scope['user']
        grp = 'comment_like_notifications_{}'.format(user.username)
        await self.channel_layer.group_discard(grp, self.channel_name)  # Remove user from the group

    # Function to send a notification
    async def notify(self, event):
        await self.send_json(event)

    # Function to send all notifications
    async def all_notifications(self, event):
        await self.send_json(event)

    # Function to handle anonymous users
    async def anonymous_user(self, event):
        await self.send_json(event)

    # Receive function to handle incoming WebSocket messages (currently commented out)
    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        data = json.loads(text_data)
        # if data['command'] == 'fetch_like_comment_notifications':
        #     await self.fetch_notifications()
