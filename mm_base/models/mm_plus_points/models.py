"""
from django.db import models
from ..core_models import Player


class PlusPlayer(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, primary_key=True, related_name='plus')
    num_points = models.IntegerField(default=0)
"""
