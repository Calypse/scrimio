from django.db import models, OperationalError
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..app_settings import TEAM_SIZE, NUM_TEAMS, ELO_DEFAULT_FAIRNESS_THRESHOLD, REGIONS


class Player(models.Model):
    """ Django User Extension for MM system """
    user = models.OneToOneField(User, related_name=("%s_mm_user" % "REPLACE_ME"), primary_key=True)
    elo = models.IntegerField(default=2500)  # Trueskill MU
    elo_weight = models.FloatField(default=50)  # Trueskill SIGMA


class Team(models.Model):
    """ Matchmaker Team """
    name = models.SlugField(max_length=20)
    players = models.ManyToManyField(Player, related_name="teams")
    captain = models.ForeignKey(Player, related_name="captain")

    def get_avg_elo(self):
        """ Returns the team's average elo for rating """
        elo_sum = 0.0
        for player in self.players.all():
            elo_sum = elo_sum + player.elo
        return elo_sum / len(self.players.all())


class Match(models.Model):
    """ Matchmaker Match Session Instance """
    # Participants
    teams = models.ManyToManyField(Team, related_name="matches", through='MatchTeamSlot')
    players = models.ManyToManyField(Player, related_name="matches", through='MatchRosterSlot')
    # Results
    declared_results = models.CharField(max_length=2) # ordered string of 1's (W) and 0's (L) of team's declared results
    winner = models.ForeignKey(Team, related_name="won_matches")
    # Status
    is_disputed = models.BooleanField(default=False)
    # Data
    start_time = models.DateTimeField(default=None, null=True, blank=True)
    end_time = models.DateTimeField(default=None, blank=True, null=True)

    # UPDATE
    def add_party(self, party):
        # If party is queued and not in a match
        if party.current_match is None and party.is_queued:
            self.players.add(party.players.all()) # add players to match list roster
            party.lock_to_match(self)
        else:
            raise ValidationError(
                _('Party is in a match or is currently not queued'),
                code='match_party_not_queued',
            )

    def remove_party(self):
        pass

    def start_match(self):
        if self.start_time is None:
            if self.players.count() == TEAM_SIZE*2:
                if self.teams.count() == NUM_TEAMS:
                    self.start_time = timezone.now()
                    self.save()

    def end_match(self):
        """End the match and commit into the ELO system"""
        # Abort if not enough teams
        if self.teams.count() != NUM_TEAMS:
            return False
        team_1 = self.teams.all()[0]
        team_2 = self.teams.all()[1]

        # Both Teams declared a result
        if team_1.result is not None and team_2.results is not None:
            # Both declared same result
            if team_1.result == team_2.result:
                self.is_disputed = True
                self.end_time = timezone.now()
            else:
                # Teams declared accurately
                self.winner = team_1 if team_1.result else team_2
        # One Team did NOT declare a result
        elif team_1.result != team_2.result:
            # One team declared accurately, extrapolate
            self.winner = team_1 if team_1.result else team_2
        # Nobody Declared a result
        else:
            self.is_disputed = True
            self.end_time = timezone.now()
        self.save()
        # Skill ELO call
        return True

    def flag_disputed(self, flag=True):
        self.is_disputed = flag

    def invalidate_match(self):
        if self.end_time is not None:
            for player in self.players.all():
                player.elo = (player.elo + player.elo_modifier * -1) # WATCH THIS LINE, ACCESSING PLAYER ODDLY
                player.elo_modifier = 0
                player.save()

    def get_declared_results(self):
        return [float(ch) for ch in self.declared_results]

    def get_elo_modifiers(self):
        return [int(player.elo_modifier) for player in self.players]

    def is_match_start_valid(self):
        """Is the match ready to be started?"""
        if self.players.count() == TEAM_SIZE * 2: # Enough players
            if self.teams.count() == NUM_TEAMS:   # Enough teams
                if None not in (self.start_time, self.end_time): # Match has not commenced
                    return True

        return False

    def is_match_invalid(self):
        """Is the match invalid or able to be invalidated?"""
        if self.end_time is not None:   # if match is over
            if self.get_elo_modifiers().contains(0): # if a Team's elo was not modified from match
                return True

        return False

    def is_match_over(self):
        return self.end_time is not None


class MatchRosterSlot(models.Model):
    """ Instance of Player's registration to a Match """
    player = models.ForeignKey(Player)
    match = models.ForeignKey(Match)
    team = models.ForeignKey(Team)
    elo_modifier = models.DecimalField(default=0.0, decimal_places=2, max_digits=8)


class MatchTeamSlot(models.Model):
    """ Instance of a Team's registration and decision to a Match """
    match = models.ForeignKey(Match)  # Match this slot belongs to
    team = models.ForeignKey(Team)  # Team that is registered to that match
    result = models.BooleanField(default=False)  # Did the team declare W / L (1 / 0)
    invalid = models.BooleanField(default=False)  # Was the result disputed and not upheld?


class Party(models.Model):
    """ Used to mutex lock players in the Queue """
    team = models.OneToOneField(Team, related_name="current_party")
    players = models.ForeignKey(Player, related_name="current_party")
    current_match = models.ForeignKey(Match, related_name="parties")
    is_queued = models.BooleanField(default=False)
    is_expedited = models.BooleanField(default=False)
    expedited_fairness = models.IntegerField(default=ELO_DEFAULT_FAIRNESS_THRESHOLD)
    region = models.CharField(choices=REGIONS, blank=True, default=None, max_length=4)

    def validate_queue(self):
        if self.players.count() == TEAM_SIZE and self.is_queued:
            return True

        return False

    def add_player(self, player):
        # If the party is already full
        if self.players.count() >= TEAM_SIZE:
            raise ValidationError(
                _('Party is at capacity. Max Players: %(max_players)'),
                code='party_at_capacity',
                params={'max_players': TEAM_SIZE},
            )

        if player.current_party is None:
            self.players.add(player)
        else:
            raise ValidationError(
                _('Player %(username) is already in a party'),
                code='party_mutex',
                params={'username':player.username},
            )

    def kick_player(self, player):
        if self.players.filter(username__exact=player.username).exists():
            self.players.remove(player)
        else:
            raise OperationalError(
                _('Player %(username) is not in this party!'),
                code='party_non_member',
                params={'username': player.username},
            )

    def lock_to_match(self, match):
        if self.current_match is None:
            if match.end_time is None and match.is_disputed is False:
                self.current_match = match
                return

        raise OperationalError(
            _('Party is still locked to a Match or Match is un-joinable'),
            code='party_mutex_violation_lock',
        )

    def unlock_from_match(self):
        if self.current_match is not None:
            if self.current_match.end_time is not None:
                if self.current_match.is_disputed is False:
                    self.current_match = None
                    return
            else:
                raise OperationalError(
                    _('Match has not ended or has been disputed'),
                    code='party_mutex_violation_unlock',
                )
        else:
            raise OperationalError(
                _('Party is not currently in a Match.'),
                code='party_mutex_unneeded',
            )

    def get_avg_elo(self):
        """ Returns the party's average elo for rating """
        elo_sum = 0.0
        for player in self.players.all():
            elo_sum = elo_sum + player.elo
        return elo_sum / len(self.players.all())
