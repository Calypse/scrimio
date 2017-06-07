from django.db import models
from ..core_models import Player


class TutorMentor(models.Model):
    """ Created when a Party is a Mentor """
    player = models.OneToOneField(Player, on_delete=models.CASCADE, primary_key=True, related_name='tutor_mentor')


class TutorStudent(models.Model):
    """ Created when a Party is a Student """
    player = models.OneToOneField(Player, on_delete=models.CASCADE, primary_key=True, related_name='tutor_student')