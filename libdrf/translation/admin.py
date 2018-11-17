from django.contrib import admin

from . import models


class TranslationInline(admin.TabularInline):
    model = models.Translation


@admin.register(models.Key)
class KeyAdmin(admin.ModelAdmin):
    search_fields = ["name", "hint"]
    inlines = [TranslationInline]


@admin.register(models.Translation)
class TranslationAdmin(admin.ModelAdmin):
    search_fields = ["key__name", "content"]
    list_display = ["key", "content"]
    list_filter = ["language"]
