from django.contrib import admin
from .models import Afkiran, AfkiranDetail

class AfkiranDetailInline(admin.TabularInline):
    model = AfkiranDetail
    extra = 0

@admin.register(Afkiran)
class AfkiranAdmin(admin.ModelAdmin):
    list_display = ('id', 'sale', 'owner', 'dp_amount', 'total_nota', 'total_sortir', 'selisih', 'sisa_bayar', 'status', 'date_created')
    list_filter = ('status', 'date_created')
    inlines = [AfkiranDetailInline]
