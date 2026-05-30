# catalog/models.py
from django.db import models


class Product(models.Model):
    # ── Identity ─────────────────────────────────────────
    sku          = models.CharField(max_length=100)
    brand        = models.CharField(max_length=200)
    product_name = models.CharField(max_length=500)
    variant      = models.CharField(max_length=200, null=True, blank=True)

    # ── Product details ──────────────────────────────────
    perfume_type = models.CharField(max_length=50, default="Unknown")
    gender       = models.CharField(max_length=20, default="Unknown")
    ml           = models.IntegerField(null=True, blank=True)
    barcode      = models.CharField(max_length=100, null=True, blank=True)

    # ── Pricing ──────────────────────────────────────────
    sale_price     = models.IntegerField(null=True, blank=True)
    original_price = models.IntegerField(null=True, blank=True)
    available      = models.BooleanField(default=True)

    # ── Source ───────────────────────────────────────────
    source_site = models.CharField(max_length=200)
    source_url  = models.URLField(max_length=500)
    scraped_at  = models.DateField()

    class Meta:
        # Same product from same source = one row
        unique_together = ["sku", "source_site"]
        ordering = ["brand", "product_name"]

    def __str__(self):
        return f"{self.brand} — {self.product_name} ({self.ml}ml)"