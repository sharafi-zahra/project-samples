import random

from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'grouping'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    TOTAL_ROUNDS = 7
    EXP_ROUNDS_RANGE = {
        'exp_trust': range(0, 4),
        'exp_ultimatum': range(4, 6),
        'exp_prisoners_dilemma': range(6, 7),
    }


def grouping(players, rounds):
    fixed_list = players[0::2]
    shift_list = players[1::2]

    random.shuffle(fixed_list)
    random.shuffle(shift_list)

    grouping_matrixes = list()
    for i in range(rounds):
        matrix = [[i, j] for i, j in zip(fixed_list, shift_list)]
        random.shuffle(matrix)
        grouping_matrixes.append(matrix)
        shift_list = [shift_list[-1]] + shift_list[:-1]

    return grouping_matrixes


class Subsession(BaseSubsession):
    pass


def creating_session(subsession):
    players = subsession.get_players()
    # if len(players) < 14:
    #         print('\n\tWARNING: "Perfect Stranger" matching in this experiment requires at least 14 participants!\n')

    players = [i for i in range(1, len(players) + 1)]
    grouping_matrixes = grouping(players, C.TOTAL_ROUNDS)
    subsession.session.grouping_matrixes = grouping_matrixes


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass



page_sequence = []
