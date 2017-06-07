from django.db import models
from django.contrib.auth.models import User


class PlusUser(models.Class):
    """ Represents a User's Plus Membership Status """
    player = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    is_active = models.BooleanField(default=False)
    signup_date = models.DateField(default=None, blank=True, null=True)  # If renewal / signup is None, isActive = False
    renewal_date = models.DateField(default=None, blank=True, null=True)
    renewal_type = models.ForeignKey(default=0, max_digits=2, )  # Month-To-Month, 6-Month, 12-Month, Special Promo, etc


class PlusRenewal(models.Class):
    """ Plus Renewal Program """
    name = models.CharField(default="")
    duration = models.IntegerField(default=1, max_digits=2)
    price = models.DecimalField(default=0.00, max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=False)  # Can you signup for this currently?
