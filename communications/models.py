import uuid  # Importing the uuid module for generating unique identifiers

from django.contrib.auth import get_user_model  # Importing the function to get the User model
from django.db import models  # Importing Django's models module

User = get_user_model()  # Getting the User model dynamically

# Creating a model for Chat Rooms
class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Unique identifier for the room
    author = models.ForeignKey(User, related_name='author_room', on_delete=models.CASCADE)  # Author of the room
    friend = models.ForeignKey(User, related_name='friend_room', on_delete=models.CASCADE)  # Friend in the room

# Creating a model for Messages within a Room
class Message(models.Model):
    author = models.ForeignKey(User, related_name='author_messages', on_delete=models.CASCADE)  # Message author
    friend = models.ForeignKey(User, related_name='friend_messages', on_delete=models.CASCADE)  # Message recipient
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.DO_NOTHING)  # Room associated with message
    message = models.TextField()  # Content of the message
    timestamp = models.DateTimeField(auto_now_add=True)  # Timestamp of when the message was created

    def __str__(self):
        return self.message + " " + str(self.timestamp)  # String representation of the message and its timestamp
