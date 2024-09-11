from django.contrib import admin

from tenders.models import Employee, Organization


# Register your models here.
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'first_name', 'last_name', 'created_at', 'updated_at']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'type']