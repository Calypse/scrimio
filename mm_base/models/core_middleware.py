from ..app_settings import ELO_EXPEDITED_FAIRNESS_MODIFIER
""" -----------------------------------------------------------------------
                                MIDDLEWARE
    ------------------------------------------------------------------- """


def mm_core_process_all_queues(queue_list):
    """ Calls process on all queues in the current stack """
    for queue in queue_list:
        mm_core_process_queue_segment(queue)


def mm_core_process_queue_segment(queue_dict, queue_queryset, logger):
    """ Creates matches from a queue of parties sorted by match elo """
    queue_segment = list(queue_queryset)  # Extract parties from segment
    segment_size = len(queue_segment)
    matches = []  # Holds created match objects
    unmatched_parties = []  # Teams that matches could not be found for

    # Empty Segment
    if segment_size < 1:
        return

    # Remove all parties from Queue
        queue_queryset.update(is_queued=False)

    while queue_segment:
        # Must be a pair of teams to attempt a match
        if len(queue_segment) < 2:
            # Add hanging team to unmatched teams
            unmatched_parties.append(queue_segment.pop(0))
            break
        else:
            # Get potential pair
            party = queue_segment[0]
            next_party = queue_segment[1]

            # Match team based on fairness, or force if expedited pass threshold is met
            if skill_is_match_or_forced(party, next_party):
                new_match = mm_create_new_match(party, next_party)

                if new_match is not None:
                    matches.append(new_match)
                    queue_segment.pop(0)
                    queue_segment.pop(0)
                else:
                    # Pass over this team if not fair
                    unmatched_parties.append(queue_segment.pop(0))
            else:
                # Pass over this team if not fair
                unmatched_parties.append(queue_segment.pop(0))

    print("\n------------------------------")
    print("Queue Batching Results")
    print("------------------------------")
    print("Total Teams in Batch: %s" % segment_size)
    print("Total Matches Found: %s" % len(matches))
    print("Total Unmatched Parties: %s\n" % len(unmatched_parties))

    print("Batch Success Rate: {:.1%}\n".format((len(matches) * 2) / segment_size))

    return len(matches)  # Return number of matches created


def mm_core_clean_queue(queue_segment_queryset):
    """ Expedite teams that were not matched """
    unmatched_parties = queue_segment_queryset.all()

    for party in unmatched_parties:
        # Expedite team and adjust their fairness range
        party.is_expedited = True
        party.expedited_fairness = (party.expidited_fairness - ELO_EXPEDITED_FAIRNESS_MODIFIER)
        party.is_queued = True
        party.save()
