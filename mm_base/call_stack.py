import logging

from .app_settings import APP_NAME
from .middleware import MM_QUEUE_STACK, MM_RESULT_STACK

""" -----------------------------------------------------------------------
                                  STACK
    ------------------------------------------------------------------- """


def stack_atomic_call_middleware(q_dict, q_queryset, logger, middleware):
    """ Calls the middleware function atomically.
            * Returns cached queue on error or None """
    cached_q_dict = q_dict[:]
    cached_q_query = q_queryset.all()

    try:
        middleware(q_dict, q_queryset, logger)
    except:
        logger.error('MM_STACK: Middleware exception occurred in %s' % middleware.__name__)
        return [cached_q_dict, cached_q_query]

    return None


def call_stack(queue_segment_queryset):
    """ Calls the middleware stack to build queues """
    q_queryset = queue_segment_queryset
    q_dict = {}  # dictionary of player lists / queues
    stack_logger = logging.getLogger('%s.mm_call_stack' % APP_NAME)  # logger instance

    for func in MM_QUEUE_STACK:
        cached_queue = stack_atomic_call_middleware(q_dict, q_queryset, stack_logger, func)
        # Restore previous Q state if middleware exception occurs
        if cached_queue is not None:
            q_dict = cached_queue[0]
            q_queryset = cached_queue[1]


def call_result_stack(match):
    """ Calls the result stack to process matches """
    stack_logger = logging.getLogger('%s.mm_result_stack' % APP_NAME)  # logger instance

    for func in MM_RESULT_STACK:
        func(match, stack_logger)

"""
def mm_build_sub_queue(q_dict, original_q, exclusion_list, q_name, logger):
    # Builds queue and adds it to the q_dict
    if q_dict[q_name] is None:  # Protect from dict collision
        excluded_ids = [obj.id for obj in exclusion_list]
        updated_q = original_q.exclude(id__in=excluded_ids)  # Update the main queue
        q_dict[q_name] = original_q.filter(id__in=excluded_ids)  # Add queue to dict
        logger.info('Sub-queue %s was built' % q_name)
        return updated_q

    logger.error('Sub-queue named %s already exists!' % q_name)
    return None
"""
