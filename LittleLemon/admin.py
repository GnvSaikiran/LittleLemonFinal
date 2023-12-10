from django.contrib import admin
from .models import Booking, Menu

admin.site.register(Booking)

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ['name', 'price']
    search_fields = ['name']
