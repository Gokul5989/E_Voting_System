# Register your models here.
from django.contrib import admin
from .models import UserProfile, PoliticianPromise, Vote, Notification

admin.site.register(UserProfile)
admin.site.register(PoliticianPromise)
admin.site.register(Vote)
admin.site.register(Notification)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'voter_id', 'is_approved')
    search_fields = ('user__username', 'voter_id', 'role')
