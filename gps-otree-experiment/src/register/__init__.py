import re
from collections import defaultdict

from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'register'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    id_ = models.StringField(label="Please enter your ID:")


def id__error_message(player, value):
    if not re.match(r'^\d+$', value):
        return 'ID must be numberic!'



# PAGES
class Welcome(Page):
    pass


class Register(Page):
    form_model = 'player'
    form_fields = ['id_']

    @staticmethod
    def live_method(player, data):
        registerations = defaultdict(list)
        players = player.subsession.get_players()

        error = id__error_message(player, data)
        if error:
            player.id_ = None
            return {player.id_in_group: {'code': 'invalid', 'content': error}}

        player.id_ = data

        for p in players:
            id_ = p.field_maybe_none('id_')
            if id_:
                registerations[id_].append(p.id_in_group)

        players_with_duplicate_id = []
        for player_ids in registerations.values():
            if len(player_ids) > 1:
                players_with_duplicate_id.extend(player_ids)

        if not players_with_duplicate_id:
            for _player in players:
                if _player.field_maybe_none('id_') in [None, '', 0]:
                    break
            else:
                return {0: {'code': 'procced'}}

        return {
            player_id: {'code': 'invalid', 'content': 'Duplicate ID!'}
            for player_id in players_with_duplicate_id
        }

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.participant.set_label(player.id_)



page_sequence = [
    Welcome,
    Register,
]
