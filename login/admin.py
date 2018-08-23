import csv

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.http import HttpResponse

from .models import User


class UserCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('email',)
        field_classes = {'email': forms.EmailField}


class UserChangeForm(UserChangeForm):

    class Meta:
        model = User
        fields = ('email', 'password', 'is_active', 'is_verified', 'is_staff')
        field_classes = {'email': forms.EmailField}


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'is_staff', 'is_superuser', 'is_active', 'is_verified', 'created')
    list_filter = ('is_staff', 'is_active', 'is_verified')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2')}),
    )
    search_fields = ('email',)
    ordering = ('email',)
    actions = ('export_email',)

    def export_email(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=users.csv'
        writer = csv.writer(response)
        writer.writerow(['email'])
        for obj in queryset:
            writer.writerow([obj.email])
        return response
    export_email.short_description = "Export all email adresses"


# Now register the new UserAdmin...
admin.site.register(User, UserAdmin)
