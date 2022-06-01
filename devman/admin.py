from django.contrib import admin
from devman.models import Student, Manager, Team

admin.site.register(Student)

@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'starttime', 'finishtime']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'title', 'date']
    list_filter = ['date']
