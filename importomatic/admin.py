from django.contrib import admin
from models import Matching

class MatchingAdmin(admin.ModelAdmin):
    pass


admin.site.register(Matching, MatchingAdmin)
