from django.db import models

from common.models import TimeStampedModel


class Country(TimeStampedModel):
    iso_code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=128)
    native_name = models.CharField(max_length=128, blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "countries"
        verbose_name_plural = "Countries"
        indexes = [
            models.Index(fields=["is_active", "name"]),
        ]

    def __str__(self) -> str:
        return self.name
