import trueskill
import math
from django.utils import timezone
from .skill import skill_is_match_or_forced
from .models import Match, Party, Player
# from .skill import skill_is_match_or_forced, skill_commit_match_result
from .app_settings import ELO_DEFAULT_FAIRNESS_THRESHOLD, ELO_AVG_RATING, ELO_RANK_INCREMENT, \
    ELO_INCREMENT_RANGE, MM_MATCH_MAX_DURATION, ELO_EXPEDITED_FAIRNESS_MODIFIER


def mm_setup_environment(mu=ELO_AVG_RATING, sigma=ELO_RANK_INCREMENT, beta=ELO_INCREMENT_RANGE, tau=5, draw_prob=0.10):
    """ Sets up the global environment for Trueskill """
    trueskill.setup(mu=mu, sigma=sigma, beta=beta, tau=tau, draw_probability=draw_prob)


def mm_create_new_match(parties):
    """ Creates Match containing Teams """
    new_match = Match.objects.create()  # Spawn Match

    for party in parties:
        new_match.teams.add(party.team)  # Add to match
        # Reset MM Params (De-Expedite)
        if party.is_expidited:
            party.is_expedited = False
            party.expedited_fairness = ELO_DEFAULT_FAIRNESS_THRESHOLD
            party.current_match = new_match
            party.save()

    new_match.save()
    return new_match


def mm_get_all_disputed_matches():
    """Returns ALL disputed matches"""
    return Match.objects.filter(is_disputed=True).all()


def mm_get_all_queued_parties():
    """ Returns all team in queue """
    return Party.objects.all().filter(is_queued=True, current_match=None)


def mm_close_all_expired_matches():
    """Closes all currently expired matches in game's MM system"""
    expired_matches = mm_get_all_expired_matches()

    for match in expired_matches:
        mm_process_expired_match(match)


def mm_get_all_expired_matches():
    """Retrieves all currently expired matches in game's MM system"""

    # When the earliest expired match could start
    expired_threshold = timezone.now() - timezone.timedelta(minutes=MM_MATCH_MAX_DURATION)
    expired_matches = Match.objects.filter(end_time=None).filter(start_time_lt=expired_threshold)

    return expired_matches


def mm_process_expired_match(match):
    """ Process expired match before Match save() """

    # Test if match is expired via time
    if timezone.now() >= match.start_time + timezone.timedelta(minutes=MM_MATCH_MAX_DURATION):
        match.end_time = timezone.now()
        match.save()


def mm_force_end(match):
    """ Forces an end_time to be assigned """
    match.end_time = timezone.now()
    match.save()


def mm_get_skill_curve_ends():
    """ Returns the highest and lowest ELO bracket, rounded to the ELO_RANK_INCREMENT
        Note: This exists in MM to avoid circular import. Originally in skill.py
    """
    low_elo = Player.objects.order_by('elo').first().elo
    high_elo = Player.objects.order_by('-elo').first().elo

    lowest_range = mm_get_closest_increment(low_elo)
    highest_range = mm_get_closest_increment(high_elo)

    return lowest_range, highest_range


def mm_get_closest_increment(elo, rank_increment=ELO_RANK_INCREMENT):
    """ Gets the rank increment closest to elo """
    return int(math.floor(elo / float(rank_increment))) * rank_increment

""" ---------------------------------------------
                    MIDDLEWARE
    --------------------------------------------- """


def mm_process_queue_segment(queue_segment_queryset):
    """ Creates matches from a queue of parties sorted by match elo """
    queue_segment = list(queue_segment_queryset)  # Extract parties from segment
    segment_size = len(queue_segment)
    matches = []  # Holds created match objects
    unmatched_parties = []  # Teams that matches could not be found for

    # Empty Segment
    if segment_size < 1:
        return

    # Remove all parties from Queue
    queue_segment_queryset.update(is_queued=False)

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


def mm_clean_queue(queue_segment_queryset):
    """ Expedite teams that were not matched """
    unmatched_parties = queue_segment_queryset.all()

    for party in unmatched_parties:
        # Expedite team and adjust their fairness range
        party.is_expedited = True
        party.expedited_fairness = (party.expidited_fairness - ELO_EXPEDITED_FAIRNESS_MODIFIER)
        party.is_queued = True
        party.save()

'''
def mm_process_match_result(match):
    """
    Processes declared match results
        - Sets match winner
        - Sets end_time
        - Flags disputed matches
        - Adjusts ELO
        - Records ELO adjustments
    """

    # Flag disputed match if both teams announced they won or lost
    if match.team_1_result == match.team_2_result:
        match.is_disputed = True
        match.end_time = timezone.now()

    # Otherwise, if a winner has not been declared but is ready to be assigned
    elif match.winner is None:
        match.end_time = timezone.now()
        teams = match.teams.all()
        match.winner = teams[0] if match.team_1_result else teams[1]

        # Modify competitor's ELOs based on Match result
        if len(match.teams.all()) > 1:
            teams[0].release_team_from_queue()
            teams[1].release_team_from_queue()

            # Record elo result modification
            elo_deltas = skill_commit_match_result(teams[0], teams[1], match.team_1_result)
            match.team_1_elo_modifier = elo_deltas[0]
            match.team_2_elo_modifier = elo_deltas[1]
        # else:
            # raise ValidationError("A match cannot conclude with only 1 competitor")
'''
