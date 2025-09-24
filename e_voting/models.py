from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    class Role(models.TextChoices):
        PUBLIC = 'public', 'Public'
        POLITICIAN = 'politician', 'Politician'

    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices)
    voter_id = models.CharField(max_length=10, unique=True, null=True, blank=True)

    party = models.CharField(
        max_length=1,
        choices=[('A', 'Party A'), ('B', 'Party B'), ('C', 'Party C')],
        null=True, blank=True
    )
    is_approved = models.BooleanField(default=False)
    image = models.ImageField(upload_to='politician_images/', null=True, blank=True)  

    def __str__(self):
        return self.user.username


class PoliticianPromise(models.Model):
    politician = models.ForeignKey(User, on_delete=models.CASCADE)
    promise_text = models.TextField()

    def __str__(self):
        return f"Promise by {self.politician.username}"

class Vote(models.Model):
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    politician = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_votes')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.voter.username} voted for {self.politician.username}"

# models.py
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class Result(models.Model):
    winner = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    votes = models.IntegerField()
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
