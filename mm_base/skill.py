"""
Skill ranking implementation for Matchmaking
"""
from trueskill import Rating, quality, rate
from .app_settings import ELO_DEFAULT_FAIRNESS_THRESHOLD, ELO_EXPEDITED_FAIRNESS_MODIFIER, ELO_EXPEDITED_MAX_PASSES


def skill_build_party_rating(party):
    """ Builds an array of Rating() objects for team roster """
    party_arr = []

    if party is not None:
        for player in party.players.all():
            party_arr.append(Rating(mu=player.elo, sigma=player.elo_weight))
    return party_arr


def skill_calculate_match_quality(party_1_roster, party_2_roster):
    """
    Calculates quality of match between 2 rosters
        - Takes 2 arrays of Rating objects
    """
    return quality([tuple(party_1_roster), tuple(party_2_roster)])


def skill_is_match(party_1, party_2, match_threshold=None):
    """ Test if match meets the available threshold """

    # Get the minimum fairness acceptable to match teams
    threshold = match_threshold if match_threshold is not None else skill_get_fairness_threshold()
    party_rating_1 = skill_build_party_rating(party_1)
    party_rating_2 = skill_build_party_rating(party_2)
    result = skill_calculate_match_quality(party_rating_1, party_rating_2)
    print('{:.1%} chance to draw'.format(result))

    if result >= threshold:
        return True

    return False


def skill_is_match_or_forced(party_1, party_2):
    """ Tests if match or should be forced """

    # Get the fairness threshold where match is forced
    exp_fairness_threshold = (ELO_DEFAULT_FAIRNESS_THRESHOLD - (ELO_EXPEDITED_FAIRNESS_MODIFIER *
                                                                ELO_EXPEDITED_MAX_PASSES))
    threshold = skill_get_fairness_threshold(party_1, party_2)

    # If forced or matched
    if threshold <= exp_fairness_threshold or skill_is_match(party_1, party_2, threshold):
        return True

    return False


def skill_get_fairness_threshold(party_1, party_2=None):
    """
    Returns lowest fairness threshold available

        - Defaults to ELO_DEFAULT_FAIRNESS_THRESHOLD
        - Can take a match up or singular team
    """

    def lowest_fairness(party, curr_fairness):
        if (party is not None and party.is_expidited
        and party.expidited_fairness < curr_fairness):
            return party.expidited_fairness
        else:
            return curr_fairness

    return lowest_fairness(party_2, lowest_fairness(party_1, ELO_DEFAULT_FAIRNESS_THRESHOLD))


def skill_commit_match_result(party_1, party_2, match_1_result):
    """
    Adjust team's elo based on result
    - Saves Player Models

    Returns delta in ELO
    """
    party_1_skill = skill_build_party_rating(party_1)
    party_2_skill = skill_build_party_rating(party_2)
    party_rosters = [party_1.players.all(), party_2.players.all()]
    result_arr = [0, 1] if match_1_result else [1, 0]
    result = rate([party_1_skill, party_2_skill], ranks=result_arr)
    p_idx = 0
    t_idx = 0
    elo_deltas = [abs(result[0][0].mu - party_rosters[0][0].elo), abs(result[1][0].mu - party_rosters[1][0].elo)]

    for roster in party_rosters:
        for player in roster:
            print("%s -> %s" % (int(player.elo), int(result[t_idx][p_idx].mu),))
            player.elo = int(result[t_idx][p_idx].mu)
            player.elo_weight = float(result[t_idx][p_idx].sigma)
            player.save()
            p_idx += 1

        t_idx += 1  # Increase team index
        p_idx = 0  # Reset player index

    return elo_deltas
