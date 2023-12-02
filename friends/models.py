# Import necessary Django modules and classes
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q

# Import custom exceptions and signals related to friendship
from friends.exceptions import AlreadyFriendsError, AlreadyExistsError
from friends.signals import friendship_request_created, friendship_removed, friendship_request_viewed, \
    friendship_request_canceled, friendship_request_accepted

# Import User model from accounts
from accounts.models import User

# Define a manager for handling notifications
class NotificationManager(models.Manager):

    # Method to get the count of unread notifications for a user
    def user_unread_notification_count(self, user) -> int:
        if not user:
            return 0
        return self.filter(is_read=False, recipient=user).count()

# Define a manager for handling friendships
class FriendshipManager(models.Manager):
    """ Friendship manager """

    # Method to retrieve a list of all friends for a user
    def friends(self, user):
        qs = (
            Friend.objects.select_related("from_user", "to_user")
                .filter(to_user=user)
                .all()
        )
        friends = [u.from_user for u in qs]
        return friends

    # Method to retrieve a list of friendship requests for a user
    def requests(self, user):
        qs = (
            FriendshipRequest.objects.select_related("from_user", "to_user")
                .filter(to_user=user)
                .all()
        )
        requests = list(qs)
        return requests

    # Method to retrieve a list of friendship requests sent by a user
    def sent_requests(self, user):
        qs = (
            FriendshipRequest.objects.select_related("from_user", "to_user")
                .filter(from_user=user)
                .all()
        )
        requests = list(qs)
        return requests

    # Method to retrieve a list of friendship requests received by a user
    def got_friend_requests(self, user):
        qs = (
            FriendshipRequest.objects.select_related("from_user__profile", "to_user")
                .filter(to_user=user)
                .all()
        )
        unread_requests = list(qs)
        return unread_requests

    # Method to retrieve a list of unread friendship requests for a user
    def unread_requests(self, user):
        qs = (
            FriendshipRequest.objects.select_related("from_user", "to_user")
                .filter(to_user=user, viewed__isnull=True)
                .all()
        )
        unread_requests = list(qs)
        return unread_requests

    # Method to get the count of unread friendship requests for a user
    def unread_request_count(self, user):
        count = FriendshipRequest.objects.select_related("from_user", "to_user").filter(to_user=user,
                                                                                        viewed__isnull=True).count()
        return count

    # Method to retrieve a list of read friendship requests for a user
    def read_requests(self, user):
        qs = (
            FriendshipRequest.objects.select_related("from_user", "to_user")
                .filter(to_user=user, viewed__isnull=False)
                .all()
        )
        read_requests = list(qs)
        return read_requests

    # Method to retrieve a list of rejected friendship requests for a user
    def rejected_requests(self, user):
        qs = (
            FriendshipRequest.objects.select_related("from_user", "to_user")
                .filter(to_user=user, rejected__isnull=False)
                .all()
        )
        rejected_requests = list(qs)
        return rejected_requests

    # Method to retrieve a list of unrejected friendship requests for a user
    def unrejected_requests(self, user):
        qs = (
            FriendshipRequest.objects.select_related("from_user", "to_user")
                .filter(to_user=user, rejected__isnull=True)
                .all()
        )
        unrejected_requests = list(qs)
        return unrejected_requests

    # Method to get the count of unrejected friendship requests for a user
    def unrejected_request_count(self, user):
        count = FriendshipRequest.objects.select_related("from_user", "to_user").filter(to_user=user,
                                                                                        rejected__isnull=True).count()
        return count

    # Method to create a friendship request between two users
    def add_friend(self, from_user, to_user, message=None):
        if from_user == to_user:
            raise ValidationError("Users cannot be friends with themselves")

        if self.are_friends(from_user, to_user):
            raise AlreadyFriendsError("Users are already friends")

        if FriendshipRequest.objects.filter(from_user=from_user, to_user=to_user).exists():
            raise AlreadyExistsError("You already requested friendship from this user.")

        if FriendshipRequest.objects.filter(from_user=to_user, to_user=from_user).exists():
            raise AlreadyExistsError("This user already requested friendship from you.")

        if message is None:
            message = ""

        request, created = FriendshipRequest.objects.get_or_create(
            from_user=from_user, to_user=to_user
        )

        if created is False:
            raise AlreadyExistsError("Friendship already requested")

        if message:
            request.message = message
            request.save()

        friendship_request_created.send(sender=request)

        return request

    # Function to remove a friendship relationship between two users
    def remove_friend(self, from_user, to_user):
        """ Destroy a friendship relationship """

        # Attempt to retrieve the friendships based on the given users
        try:
            qs = Friend.objects.filter(
                Q(to_user=to_user, from_user=from_user) | Q(to_user=from_user, from_user=to_user))
            distinct_qs = qs.distinct().all()

            # If friendships exist, trigger the 'friendship_removed' signal and delete the relationships
            if distinct_qs:
                friendship_removed.send(
                    sender=distinct_qs[0], from_user=from_user, to_user=to_user
                )
                qs.delete()
                return True
            else:
                return False
        except Friend.DoesNotExist:
            return False

    # Method to check if two users are friends
    def are_friends(self, user1, user2):
        """ Are these two users friends? """
        try:
            Friend.objects.get(to_user=user1, from_user=user2)
            return True
        except Friend.DoesNotExist:
            return False

# Definition of the FriendshipRequest model
class FriendshipRequest(models.Model):
    """ Model to represent friendship requests """

    # Fields to represent the sender and receiver of the friendship request
    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="friendship_requests_sent",
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="friendship_requests_received",
    )

    # Additional fields for the friendship request model
    message = models.TextField(_("Message"), blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    rejected = models.DateTimeField(blank=True, null=True)
    viewed = models.DateTimeField(blank=True, null=True)

    # Meta information about the FriendshipRequest model
    class Meta:
        verbose_name = _("Friendship Request")
        verbose_name_plural = _("Friendship Requests")
        unique_together = ("from_user", "to_user")

    # Method to accept a friendship request
    def accept(self):
        """ Accept this friendship request """

        # Create Friend instances for both users and trigger the 'friendship_request_accepted' signal
        Friend.objects.create(from_user=self.from_user, to_user=self.to_user)
        Friend.objects.create(from_user=self.to_user, to_user=self.from_user)
        friendship_request_accepted.send(
            sender=self, from_user=self.from_user, to_user=self.to_user
        )

        # Delete the current friendship request and its reverse request (if any)
        self.delete()
        FriendshipRequest.objects.filter(
            from_user=self.to_user, to_user=self.from_user
        ).delete()

        return True

    # Method to reject a friendship request
    def reject(self):
        """ reject this friendship request """
        self.rejected = timezone.now()
        self.save()
        return True

    # Method to cancel a friendship request
    def cancel(self):
        """ cancel this friendship request """
        self.delete()
        friendship_request_canceled.send(sender=self)
        return True

    # Method to mark a friendship request as viewed
    def mark_viewed(self):
        self.viewed = timezone.now()
        friendship_request_viewed.send(sender=self)
        self.save()
        return True

# Definition of the Friend model representing user friendships
class Friend(models.Model):
    # Fields representing the sender and receiver of the friendship
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friends')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    objects = FriendshipManager()  # Assigning the FriendshipManager to manage Friend instances

    # Meta information about the Friend model
    class Meta:
        verbose_name = _("Friend")
        verbose_name_plural = _("Friends")
        unique_together = ("from_user", "to_user")

    # Custom save method to prevent users from being friends with themselves
    def save(self, *args, **kwargs):
        if self.to_user == self.from_user:
            raise ValidationError("Users cannot be friends with themselves.")
        super().save(*args, **kwargs)

# Definition of the CustomNotification model
class CustomNotification(models.Model):
    # Fields for a custom notification
    type = models.CharField(default='friend', max_length=30)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=False,
        related_name='notifications',
        on_delete=models.CASCADE
    )
    # Other fields representing notification details

    objects = NotificationManager()  # Assigning the NotificationManager to manage CustomNotification instances

