from django.contrib.auth.models import User
from django.db import models
import uuid


class Employee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Organization(models.Model):
    ORGANIZATION_TYPES = [
        ('IE', 'Individual Entrepreneur'),
        ('LLC', 'Limited Liability Company'),
        ('JSC', 'Joint Stock Company'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=3, choices=ORGANIZATION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OrganizationResponsible(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    user = models.ForeignKey('Employee', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} responsible for {self.organization.name}"


class Tender(models.Model):
    SERVICE_TYPES = [
        ('Construction', 'Construction'),
        ('IT', 'IT'),
        ('Logistics', 'Logistics'),

    ]

    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
        ('In Progress', 'In Progress'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    service_type = models.CharField(max_length=50, null=True, choices=SERVICE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    organization = models.ForeignKey('Organization', null=True, on_delete=models.CASCADE)
    creator = models.ForeignKey('Employee',null=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TenderVersion(models.Model):
    tender = models.ForeignKey(Tender, related_name='versions', on_delete=models.CASCADE)
    version = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tender', 'version')


class Bid(models.Model):
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('PUBLISHED', 'Published'),
        ('CANCELED', 'Canceled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    tender = models.ForeignKey(Tender, related_name='bids', on_delete=models.CASCADE)
    organization = models.ForeignKey('Organization', related_name='bids', on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, related_name='bids', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class BidVersion(models.Model):
    bid = models.ForeignKey(Bid, related_name='versions', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    version = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('bid', 'version')
        ordering = ['-version']

    def __str__(self):
        return f"Version {self.version} of Bid {self.bid.id}"


class BidReview(models.Model):
    bid = models.ForeignKey(Bid, related_name='reviews', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE, default=1)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.author.username} for Bid {self.bid.id}"