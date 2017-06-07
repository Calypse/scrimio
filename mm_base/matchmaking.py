import trueskill
import math

from django.utils import timezone
from .models.core_models import Match, Party, Player
from .app_settings import ELO_DEFAULT_FAIRNESS_THRESHOLD, ELO_AVG_RATING, ELO_RANK_INCREMENT, \
    ELO_INCREMENT_RANGE, MM_MATCH_MAX_DURATION


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
