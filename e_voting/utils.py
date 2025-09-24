# utils.py
import random
from .models import UserProfile

def generate_voter_id():
    while True:
        voter_id = ''.join(random.choices('0123456789', k=10))
        if not UserProfile.objects.filter(voter_id=voter_id).exists():
            return voter_id
