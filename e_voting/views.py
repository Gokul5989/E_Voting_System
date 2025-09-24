from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.db import models
from django.db.models import Count
from .utils import generate_voter_id 
from django.core.mail import send_mail
from .forms import PublicRegistrationForm, PoliticianRegistrationForm, PromiseForm, AuthenticationForm
from .models import UserProfile, PoliticianPromise, Vote, Notification, Result
from django.contrib.auth.models import User

def index_view(request):
    return render(request, 'index.html')  # this is your default HTML page

# Role Checkers
def is_public(user):
    return hasattr(user, 'userprofile') and user.userprofile.role == UserProfile.Role.PUBLIC

def is_politician(user):
    return hasattr(user, 'userprofile') and user.userprofile.role == UserProfile.Role.POLITICIAN

def is_admin(user):
    return user.is_staff


# Login View
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            profile = getattr(user, 'userprofile', None)

            if profile and profile.role == UserProfile.Role.POLITICIAN and not profile.is_approved:
                messages.error(request, "Your account is pending admin approval.")
                return redirect('login')

            login(request, user)

            if user.is_staff:
                return redirect('admin_home')

            role = getattr(profile, 'role', None)
            if role == UserProfile.Role.PUBLIC:
                return redirect('public_home')
            elif role == UserProfile.Role.POLITICIAN:
                return redirect('politician_home')
            else:
                messages.error(request, "Invalid role.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})



# Logout View
def user_logout(request):
    logout(request)
    return redirect('login')


#  Register as public
def register_public(request):
    if request.method == 'POST':
        form = PublicRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])  # Hash the password
            user.save()  # ✅ Save user first

 # ✅ Generate voter ID
            voter_id = generate_voter_id()

            # Now create UserProfile with saved user
            profile=UserProfile.objects.create(user=user, role='public',voter_id=voter_id)
# ✅ Send email to user
            send_mail(
                subject="E-Voting System - Your Voter ID",
                message=f"""
Dear {user.username},

Thank you for registering with the E-Voting system.

Your unique 10-digit Voter ID is: {voter_id}

You will need this ID to cast your vote. Please keep it secure.

Regards,
E-Voting Team
""",
                from_email='gokulsakthivel59891@gmail.com',
                recipient_list=[user.email],
                fail_silently=False,
            )

            messages.success(request, "Registration successful! Voter ID has been sent to your email.")
            return redirect('login')
        else:
            print("Form Errors:", form.errors)  # Debug
    else:
        form = PublicRegistrationForm()
    return render(request, 'register_public.html', {'form': form})


# Register as politician
def register_politician(request):
    if request.method == 'POST':
        form = PoliticianRegistrationForm(request.POST, request.FILES)  # ✅ use request.FILES
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            UserProfile.objects.create(
                user=user,
                role='politician',
                is_approved=False,
                party=form.cleaned_data.get('party'),
                image=form.cleaned_data.get('image')  # ✅ save image
            )

            Notification.objects.create(
                user=User.objects.filter(is_superuser=True).first(),
                message=f"New politician {user.username} is awaiting approval."
            )

            messages.success(request, "Registration successful! Await admin approval.")
            return redirect('login')
    else:
        form = PoliticianRegistrationForm()
    return render(request, 'register_politician.html', {'form': form})


# Public Dashboard
@login_required
@user_passes_test(is_public)
def public_home(request):
    voted = Vote.objects.filter(voter=request.user).exists()
    print("Already voted?", voted)

    promises = PoliticianPromise.objects.all()
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
    politicians = UserProfile.objects.filter(role='politician', is_approved=True)

    if request.method == 'POST':
        print("POST received")

        if voted:
            messages.error(request, "You have already voted.")
            return redirect('public_home')

        voter_id = request.POST.get('voter_id')
        pol_id = request.POST.get('politician')
        print("Submitted voter_id:", voter_id)
        print("Submitted politician:", pol_id)

        # Check if voter_id matches
        try:
            profile = UserProfile.objects.get(user=request.user)
            print("Stored voter_id:", profile.voter_id)
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found.")
            return redirect('public_home')

        if voter_id != profile.voter_id:
            messages.error(request, "Invalid Voter ID.")
            return redirect('public_home')

        try:
            politician = UserProfile.objects.get(user_id=pol_id, role='politician')
        except UserProfile.DoesNotExist:
            messages.error(request, "Politician not found.")
            return redirect('public_home')

        Vote.objects.create(
            voter=request.user,
            politician=politician.user,
            timestamp=timezone.now()
        )
        messages.success(request, "Vote submitted successfully.")
        return redirect('public_home')

    return render(request, 'public_home.html', {
        'promises': promises,
        'voted': voted,
        'notifications': notifications,
        'politicians': politicians,
    })


# Politician Dashboard
@login_required
@user_passes_test(is_politician)
def politician_home(request):
    voted = Vote.objects.filter(voter=request.user).exists()
    promises = PoliticianPromise.objects.filter(politician=request.user)
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')

    profile = UserProfile.objects.get(user=request.user)

    if request.method == 'POST':
        if 'promise_text' in request.POST:
            form = PromiseForm(request.POST)
            if form.is_valid():
                promise = form.save(commit=False)
                promise.politician = request.user
                promise.save()
                messages.success(request, "Promise uploaded.")
                return redirect('politician_home')
            
        elif 'politician' in request.POST and not voted:
            voter_id_input = request.POST.get('voter_id')
            pol_id = request.POST.get('politician')

        if voter_id_input == profile.voter_id:    
            politician = get_object_or_404(UserProfile, user_id=pol_id, role=UserProfile.Role.POLITICIAN)
            Vote.objects.create(voter=request.user, politician=politician.user, timestamp=timezone.now())
            messages.success(request, "Vote submitted successfully.")
            return redirect('politician_home')
        else:
                messages.error(request, "Invalid Voter ID.")

    form = PromiseForm()
    return render(request, 'politician_home.html', {
        'promises': promises,
        'voted': voted,
        'form': form,
        'notifications': notifications,
        'profile': profile, 
    })


# Admin Dashboard
@login_required
@user_passes_test(is_admin)
def admin_home(request):
    profile = UserProfile.objects.get(user=request.user)

    # Always define users
    users = UserProfile.objects.exclude(user__is_staff=True)

    politicians = UserProfile.objects.filter(role=UserProfile.Role.POLITICIAN)
    unapproved_politicians = politicians.filter(is_approved=False)
    votes = Vote.objects.all()
    vote_results = Vote.objects.values('politician__username').annotate(total_votes=Count('id'))

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'start':
            Vote.objects.all().delete()
            request.session['voting_open'] = True
            messages.success(request, "Voting started.")

        elif action == 'stop':
            request.session['voting_open'] = False
            messages.success(request, "Voting stopped.")

        elif action == 'notify':
            tally = {p.user.username: votes.filter(politician=p.user).count() for p in politicians}
            for profile in UserProfile.objects.all():
                Notification.objects.create(
                    user=profile.user,
                    message=f"Voting Result: {tally}"
                )
            messages.success(request, "Notifications sent.")

        return redirect('admin_home')

    context = {
        'users': users,
        'politicians': politicians,
        'unapproved_politicians': unapproved_politicians,
        'votes': votes,
        'vote_results': vote_results,
        'voting_open': request.session.get('voting_open', False),
    }
    return render(request, 'admin_home.html', context)


@login_required
def approve_politician(request, user_id):
    if request.method == 'POST':
        profile = UserProfile.objects.get(user=request.user)
        

        target_profile = get_object_or_404(UserProfile, user__id=user_id, role='politician')
        target_profile.is_approved = True
        target_profile.user.is_active = True
        target_profile.save()
        target_profile.user.save()

# ✅ Generate voter ID if not already present
        if not target_profile.voter_id:
            target_profile.voter_id = generate_voter_id()

        target_profile.save()
        target_profile.user.save()

        # ✅ Send voter ID via email
        send_mail(
            subject="E-Voting System - You Are Approved",
            message=f"""
Dear {target_profile.user.username},

Your account as a politician has been approved in the E-Voting system.

Your unique 10-digit Voter ID is: {target_profile.voter_id}

Please use this ID to cast your vote.

Best regards,  
E-Voting Admin
""",
            from_email='gokulsakthivel59891@gmail.com',
            recipient_list=[target_profile.user.email],
            fail_silently=False,
        )

        messages.success(request, f"{target_profile.user.username} approved successfully.")
        return redirect('admin_home')  # Make sure this URL name is correct
    else:
        return HttpResponseForbidden("Only POST method is allowed.")

# Declare Results (Admin Only)
@login_required
def declare_results(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Only admin can declare results")

    vote_counts = Vote.objects.values('politician').annotate(total=models.Count('politician')).order_by('-total')

    if vote_counts:
        top = vote_counts[0]
        winner_profile = UserProfile.objects.get(user_id=top['politician'])
        message = f"{winner_profile.user.username} has won with {top['total']} votes!"
        Result.objects.create(
            winner=winner_profile,
            votes=top['total'],
            message=message
        )
        for profile in UserProfile.objects.all():
            Notification.objects.filter(user=profile.user).delete()  # Delete user’s old notifications
            Notification.objects.create(user=profile.user, message=message)

        messages.success(request, "Results declared and saved.")
    else:
        messages.error(request, "No votes to count.")

    return redirect('admin_home')

def vote_view(request, politician_id):
    if request.method == 'POST':
        entered_voter_id = request.POST.get('voter_id')
        profile = UserProfile.objects.get(user=request.user)

        if profile.voter_id != entered_voter_id:
            messages.error(request, "Incorrect Voter ID.")
            return redirect('vote_page')

        # Proceed with vote submission
        if Vote.objects.filter(voter=request.user).exists():
            messages.warning(request, "You have already voted.")
        else:
            Vote.objects.create(voter=request.user, politician_id=politician_id)
            messages.success(request, "Your vote has been submitted successfully.")

        return redirect('public_home')

    return render(request, 'vote_page.html')