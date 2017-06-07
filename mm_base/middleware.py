"""------------------------------------------
        Matchmaking Middleware Stack
   ---------------------------------------"""
from .models.core_middleware import mm_core_process_queue_segment, mm_core_clean_queue
from .models.mm_regions.middleware import *
from .models.mm_tutor.middleware import *
from .models.mm_plus_points.middleware import *

""" Dictionary of functions that make up queue
        - FUNCTION SIGNATURE:
            * pkg_func_name(queue_dict, queue_queryset, django_logger)
"""
MM_QUEUE_STACK = {
    'region_sort':              regions_sort_queues,
    'mm_tutor_process_queue':   mentor_process_queue,
    'mm_process_queue':         mm_core_process_queue_segment,
    'mm_clean_queue':           mm_core_clean_queue,
}


""" Dictionary of functions queue uses to process match results
        - FUNCTION SIGNATURE:
            * pkg_func_name(match, django_logger)
"""
MM_RESULT_STACK = {
    'plus_award_points':        plus_award_points,
}
