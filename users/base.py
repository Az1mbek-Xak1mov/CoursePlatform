"""
Abstract base models for reusability across the application.
Following DRY (Don't Repeat Yourself) principle.
"""
from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    """
    Abstract base model that provides self-updating
    'created_at' and 'updated_at' fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the record was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the record was last updated")

    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteManager(models.Manager):
    """
    Manager that returns only non-deleted objects by default.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """
    Manager that returns all objects including deleted ones.
    """
    def get_queryset(self):
        return super().get_queryset()


class SoftDeleteModel(models.Model):
    """
    Abstract base model that provides soft delete functionality.
    Instead of actually deleting records, we mark them as deleted.
    """
    is_deleted = models.BooleanField(default=False, help_text="Soft delete flag")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when the record was deleted")

    # Default manager returns only non-deleted objects
    objects = SoftDeleteManager()
    # Manager to access all objects including deleted
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard=False):
        """
        Soft delete by default. Pass hard=True for actual deletion.
        """
        if hard:
            super().delete(using=using, keep_parents=keep_parents)
        else:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save()

    def restore(self):
        """
        Restore a soft-deleted object.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class BaseModel(TimestampedModel, SoftDeleteModel):
    """
    Combines timestamped and soft delete functionality.
    Most models should inherit from this.
    """
    class Meta:
        abstract = True
