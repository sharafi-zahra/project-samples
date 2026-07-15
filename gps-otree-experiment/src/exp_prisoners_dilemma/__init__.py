from otree.api import *

from core import (
    ExpPaymentAlert,
    ControlPage,
    ControlFailedPage,
    ControlPassed,
    ControlPlayerMixin,
    SimpleWaitPage,
    PayoffWaitPage,
    set_counters,
    set_groups,
)


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'prisoners_dilemma'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 1

    CONTROL_CORRECT_ANSWERS = {
        'A': False,
        'B': cu(240),
        'C': cu(280),
    }


class Subsession(BaseSubsession):
    exp_num = models.IntegerField()


def creating_session(subsession):
    set_groups(subsession)
    set_counters(subsession)


class Group(BaseGroup):

    def set_payoffs(self):
        player1 = self.get_player_by_role('Player 1')
        player2 = self.get_player_by_role('Player 2')

        c1 = player1.contribute
        c2 = player2.contribute

        p1_punish_pp = player1.punishment_pp
        p1_punish_pn = player1.punishment_pn
        p1_punish_np = player1.punishment_np
        p1_punish_nn = player1.punishment_nn

        p2_punish_pp = player2.punishment_pp
        p2_punish_pn = player2.punishment_pn
        p2_punish_np = player2.punishment_np
        p2_punish_nn = player2.punishment_nn

        if c1 and c2:
            payoff = 480 - p2_punish_pp  - (p1_punish_pp / 3)
            player1.payoff = cu(payoff) if payoff >= 0 else cu(0)

            payoff = 480 - p1_punish_pp  - (p2_punish_pp / 3)
            player2.payoff = cu(payoff) if payoff >= 0 else cu(0)

        elif c1 and not c2:
            payoff = 240 - p2_punish_np  - (p1_punish_pn / 3)
            player1.payoff = cu(payoff) if payoff >= 0 else cu(0)

            payoff = 540 - p1_punish_pn - (p2_punish_np / 3)
            player2.payoff = cu(payoff) if payoff >= 0 else cu(0)

        elif not c1 and c2:
            payoff = 540 - p2_punish_pn - (p1_punish_np / 3)
            player1.payoff = cu(payoff) if payoff >= 0 else cu(0)

            payoff = 240 - p1_punish_np - (p2_punish_pn / 3)
            player2.payoff = cu(payoff) if payoff >= 0 else cu(0)

        elif not c1 and not c2:
            payoff = 300 - p2_punish_nn  - (p1_punish_nn / 3)
            player1.payoff = cu(payoff) if payoff >= 0 else cu(0)

            payoff = 300 - p1_punish_nn  - (p2_punish_nn / 3)
            player2.payoff = cu(payoff) if payoff >= 0 else cu(0)


class Player(BasePlayer, ControlPlayerMixin):
    CP1_A = models.BooleanField(
        label='',
        choices=[
            [True, 'True'],
            [False, 'False'],
        ],
    )
    CP1_B = models.CurrencyField(
        label='',
        min=0,
    )
    CP1_C = models.CurrencyField(
        label='',
        min=0,
    )
    CP2_A = models.BooleanField(
        label='',
        choices=[
            [True, 'True'],
            [False, 'False'],
        ],
    )
    CP2_B = models.CurrencyField(
        label='',
        min=0,
    )
    CP2_C = models.CurrencyField(
        label='',
        min=0,
    )

    contribute = models.BooleanField(
        label="<b>Your decision?</b>",
        choices=[
            [True, 'Contribute'],
            [False, 'Don’t contribute'],
        ],
        widget=widgets.RadioSelect
    )

    punishment_pp = models.CurrencyField(
        label="How many points would you like to deduct from the other participant?",
        min=0,
        max=480,
    )
    punishment_pn = models.CurrencyField(
        label="How many points would you like to deduct from the other participant?",
        min=0,
        max=540,
    )
    punishment_np = models.CurrencyField(
        label="How many points would you like to deduct from the other participant?",
        min=0,
        max=240,
    )
    punishment_nn = models.CurrencyField(
        label="How many points would you like to deduct from the other participant?",
        min=0,
        max=300,
    )

    def role(self):
        if self.id_in_group == 1:
            return 'Player 1'

        else:
            return 'Player 2'


# PAGES
class Instructions_1(Page):
    pass


class Instructions_2(Page):
    pass


class Control(ControlPage):
    pass


class ControlFailed(ControlFailedPage):
    pass


class Punishment_PP(Page):
    form_model = 'player'
    form_fields = ['punishment_pp']


class Punishment_PN(Page):
    form_model = 'player'
    form_fields = ['punishment_pn']


class Punishment_NP(Page):
    form_model = 'player'
    form_fields = ['punishment_np']


class Punishment_NN(Page):
    form_model = 'player'
    form_fields = ['punishment_nn']


class Contribution(Page):
    form_model = 'player'
    form_fields = ['contribute']


page_sequence = [
    ExpPaymentAlert,
    Instructions_1,
    Control,
    Control,
    ControlFailed,
    ControlPassed,
    Instructions_2,
    SimpleWaitPage,
    Punishment_PP,
    Punishment_PN,
    Punishment_NP,
    Punishment_NN,
    Contribution,
    PayoffWaitPage,
]
