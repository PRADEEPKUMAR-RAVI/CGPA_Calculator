from django.contrib import admin

from .models import Semester, Subject,UserResult,Department

admin.site.register(Semester)
admin.site.register(Subject)
admin.site.register(UserResult)
admin.site.register(Department)
