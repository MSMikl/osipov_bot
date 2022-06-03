from django.contrib import admin
from devman.models import Student, Manager, Team


@admin.register(Student)
class Student(admin.ModelAdmin):
    list_display = ['__str__', 'level']


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'starttime', 'finishtime']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'title', 'date', 'manager']
    list_filter = ['is_active', 'manager']
