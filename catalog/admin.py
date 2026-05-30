from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ["brand", "product_name", "ml",
                     "perfume_type", "gender",
                     "sale_price", "source_site"]
    list_filter   = ["source_site", "perfume_type",
                     "gender", "brand"]
    search_fields = ["brand", "product_name", "sku"]