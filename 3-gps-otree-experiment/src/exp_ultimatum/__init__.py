from otree.api import *

from core import (
    ExpPaymentAlert,
    ControlPage,
    ControlFailedPage,
    ControlPlayerMixin,
    ControlPassed,
    SimpleWaitPage,
    PayoffWaitPage,
    set_counters,
    set_groups,
)


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'exp_ultimatum'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 2

    ENDOWMENT = cu(500)

    CONTROL_CORRECT_ANSWERS = {
        'A': cu(500),
        'B': cu(0),
        'C': cu(0),
    }


class Subsession(BaseSubsession):
    exp_num = models.IntegerField()


def creating_session(subsession):
    set_groups(subsession)
    set_counters(subsession)


class Group(BaseGroup):

    def set_payoffs(self):
        sender = self.get_player_by_role('Sender')
        reciever = self.get_player_by_role('Reciever')

        offer = sender.offer
        min_expect = reciever.min_expect

        if offer >= min_expect:
            sender.payoff = C.ENDOWMENT - offer
            reciever.payoff = offer

        else:
            sender.payoff = 0
            reciever.payoff = 0


class Player(BasePlayer, ControlPlayerMixin):
    CP1_A = models.CurrencyField(min=0, max=1000000)
    CP1_B = models.CurrencyField(min=0, max=1000000)
    CP1_C = models.CurrencyField(min=0, max=1000000)
    CP2_A = models.CurrencyField(min=0, max=1000000)
    CP2_B = models.CurrencyField(min=0, max=1000000)
    CP2_C = models.CurrencyField(min=0, max=1000000)

    offer = models.CurrencyField(
        label="Please indicate the amount you want to send to the other person.",
        min=0,
        max=C.ENDOWMENT,
    )
    min_expect = models.CurrencyField(
        label="Please indicate the minimum amount that you are willing to accept.",
        min=0,
        max=C.ENDOWMENT,
    )

    def role(self):
        if self.id_in_group == 1:
            if self.round_number % 2 == 0:
                return 'Reciever'

            else:
                return 'Sender'

        else:
            if self.round_number % 2 == 0:
                return 'Sender'

            else:
                return 'Reciever'


# PAGES
class Instructions(Page):
    pass


class Control(ControlPage):
    pass


class ControlFailed(ControlFailedPage):
    pass


class Offer(Page):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player):
        if player.role() == 'Sender':
            return ['offer']

        elif player.role() == 'Reciever':
            return ['min_expect']


page_sequence = [
    ExpPaymentAlert,
    Instructions,
    Control,
    Control,
    ControlFailed,
    ControlPassed,
    SimpleWaitPage,
    Offer,
    PayoffWaitPage,
]
