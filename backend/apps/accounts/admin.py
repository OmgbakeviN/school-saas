from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User,SchoolMembership
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model=User
    ordering=("email",)
    list_display=("email","first_name","last_name","is_staff","is_active")
@admin.register(SchoolMembership)
class MembershipAdmin(admin.ModelAdmin):
    list_display=("user","school","role","is_active")
