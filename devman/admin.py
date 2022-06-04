from django.contrib import admin
from devman.models import Student, Manager, Team


@admin.register(Student)
class Student(admin.ModelAdmin):
    list_display = ['__str__', 'level', 'status']
    raw_id_fields = [
        'banned_students',
        'desired_students',
        'banned_manager',
        'desired_manager'
    ]
    list_filter = ['level', 'status']


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'starttime', 'finishtime']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'title', 'date', 'manager']
    list_filter = ['is_active', 'manager']
