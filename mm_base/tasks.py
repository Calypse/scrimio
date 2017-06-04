from __future__ import absolute_import, unicode_literals
from datetime import timedelta
from celery import shared_task

from django.utils import timezone
from .app_settings import MM_MATCH_MAX_DURATION

from .matchmaking import mm_process_queue_segment
from .models import Team, Match


@shared_task(name='process_queue_segment')
def task_process_match_queue_segment(segment_pk):
    """ segment_pk : List of Party pks """
    queue_segment = Team.objects.all().filter(pk__in=segment_pk)
    mm_process_queue_segment(queue_segment)


@shared_task(name='process_expired_matches')
def task_process_expired_matches():
    """ Automatically kill expired matches """
    time_threshold = timezone.now() - timedelta(hours=(MM_MATCH_MAX_DURATION/60))
    expired = Match.objects.all().filter(end_time=None, start_time__lt=time_threshold)
    expired.update(end_time=timezone.now())
