from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import PoliticianPromise, UserProfile
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from e_voting.models import UserProfile

class PublicRegistrationForm(UserCreationForm):
   
    class Meta:
        model = User
        fields = ['username','email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)  # Get user, but don't save yet
        if commit:
            user.save()  # Save the user object to DB
            # Now we can safely create the UserProfile
            UserProfile.objects.create(user=user, role=UserProfile.Role.PUBLIC)
        return user

class PoliticianRegistrationForm(UserCreationForm):
    party = forms.ChoiceField(
        choices=[('A', 'Party A'), ('B', 'Party B'), ('C', 'Party C')],
        widget=forms.RadioSelect,
        required=True
    )
    image = forms.ImageField(required=False)
    
    class Meta:
        model = User
        fields = ['username','email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        if commit:
            user.save()
            party = self.cleaned_data['party']  # ✅ Get selected party
            UserProfile.objects.create(
                user=user,
                role=UserProfile.Role.POLITICIAN,
                party=party,
                is_approved=False
            )
        return user



class PromiseForm(forms.ModelForm):
    class Meta:
        model = PoliticianPromise
        fields = ['promise_text']
