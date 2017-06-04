"""
App specific settings for Matchmaking app

Used to generalize aspects of the Matchmaker for easy deployment in other games
"""

'''
General Settings
'''
GAME_NAME = ""							# Used to specify Game Name for generated routes
TEAM_SIZE = 5 							# Number of players on a team
NUM_TEAMS = 2
APP_NAME = ("mm_%s" % GAME_NAME) 	    # Generated name of app
Q_SEGMENT_SIZE = 750					# How many teams each Celery worker will process
SUPPORTS_REGIONS = True                 # Toggle multi-region support. Turn off if each region gets it's own MM system


'''
Matchmaking Middleware Stack
'''
mm_stack = {
    'matchmaking.mm_process_queue_segment',
    'matchmaking.mm_clean_queue',
}


'''
Matchmaking Settings
'''
MM_MATCH_MAX_DURATION = 120 			# Max num minutes a match can exist
MM_NUM_MATCH_WINNERS = 1                # Number of possible winners within a match


'''
Regions
'''
REGIONS = ((None, 'Choose Region'),
           ('USW', 'US West'),
           ('USE', 'US East'),
           ('EUW', 'EU West'),
           ('EUC', 'EU Central'),
           ('EUE', 'EU East'),)


'''
Rank Settings
'''
ELO_AVG_RATING=2500						# Initial mean of ratings/elo (Trueskill mu)
ELO_RANK_INCREMENT=500					# How ranks are sequestered (Trueskill sigma)
ELO_INCREMENT_RANGE=250					# Distance in rank that guarantees 76% 'fairness' (1/2 * sigma)
ELO_MODIFIER = 25						# How elo is adjusted per game
ELO_DEFAULT_FAIRNESS_THRESHOLD = 0.45 	# Lowest match fairness is 42% change of draw
ELO_EXPEDITED_FAIRNESS_MODIFIER = 0.05 	# Decrease team's fairness threshold by 5% each time a match cannot be found
ELO_EXPEDITED_MAX_PASSES = 3 			# How many times a team can be passed over before a match is FORCED


'''
Websocket Channel Prefixes
------------------------------

String interpolate with team names to get specific channel names
'''
CHAN_TEAM_Q_STATUS = ("%s-team-status-" % GAME_NAME)
CHAN_TEAM_Q_CHAT = ("%s-team-chat-" % GAME_NAME)
CHAN_TEAM_Q_MATCH_CHAT = ("%s-team-match-chat-" % GAME_NAME)


'''
Websocket Channel Op Strings
------------------------------

Used to differentiate what operation each websocket message is asking
This value will be assigned to the "op" key in a websocket message
'''
OP_NEW_MATCH = 'new-match'
OP_CHAT_MSG = 'chat-msg'
