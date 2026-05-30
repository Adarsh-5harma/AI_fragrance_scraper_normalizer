# catalog/serializers.py
from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Product
        fields = [
            "id", "sku", "brand", "product_name", "variant",
            "perfume_type", "gender", "ml", "barcode",
            "sale_price", "original_price", "available",
            "source_site", "source_url", "scraped_at"
        ]