from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import os # Import the os module for file system operations
from django.conf import settings # Import settings to access MEDIA_ROOT

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    name = models.CharField(max_length=200, null=True)
    email = models.EmailField(unique=True, null=True)
    bio = models.TextField(null=True)

    avatar = models.ImageField(null=True, default="avatar.svg")

    USERNAME_FIELD =  'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def save(self, *args, **kwargs):
        # This method is called when a User instance is saved (created or updated).
        # We want to delete the old avatar file if the avatar is being changed.
        if self.pk: # Check if the instance already exists in the database (i.e., it's an update)
            try:
                # Retrieve the old instance from the database to compare its avatar
                old_instance = User.objects.get(pk=self.pk)
                # Check if the avatar has changed AND if the old avatar was not the default 'avatar.svg'
                if old_instance.avatar and old_instance.avatar.name != self.avatar.name and old_instance.avatar.name != 'avatar.svg':
                    # Construct the full path to the old avatar file
                    old_avatar_path = os.path.join(settings.MEDIA_ROOT, old_instance.avatar.name)
                    # Delete the old avatar file if it exists on the filesystem
                    if os.path.exists(old_avatar_path):
                        try:
                            os.remove(old_avatar_path)
                        except OSError as e:
                            # Log the error, but don't prevent the new avatar from being saved
                            print(f"Error deleting old avatar file {old_avatar_path}: {e}")
            except User.DoesNotExist:
                # This case should ideally not happen if self.pk exists, but good for robustness
                pass
        super().save(*args, **kwargs) # Call the original save method

    def delete(self, *args, **kwargs):
        # This method is called when a User instance is deleted.
        # We want to delete the associated avatar file, unless it's the default.
        if self.avatar and self.avatar.name != 'avatar.svg':
            avatar_path = os.path.join(settings.MEDIA_ROOT, self.avatar.name)
            if os.path.exists(avatar_path):
                try:
                    os.remove(avatar_path)
                except OSError as e:
                    print(f"Error deleting avatar file {avatar_path} during user deletion: {e}")
        super().delete(*args, **kwargs) # Call the original delete method

# Create your models here.

class Topic(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Room(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='participants', blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.name
    
class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    body = models.TextField()
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated', '-created']

    def __str__(self):
        return self.body[0:50]