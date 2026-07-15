import random

from otree.api import *

from core import (
    ExpPaymentAlert,
    ControlPage,
    ControlFailedPage,
    ControlPlayerMixin,
    ControlPassed,
    RiskDecision,
    SimpleWaitPage,
    PayoffWaitPage,
    set_counters,
    set_groups,
    LotteryPrize,
)


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'exp_risk'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 2

    LOTTERY_PRIZE = LotteryPrize(cu(1000), cu(0))
    POINT_LISTS = {
        1: [cu(x) for x in range(0, 1001, 50)],
        2: [cu(x) for x in (0, 45, 97, 151, 204, 247, 305, 348, 403, 449, 503, 545, 602, 649, 699, 745, 803, 855, 901, 946, 1004)],
    }

    @classmethod
    def get_point_list(cls, round_number):
        return cls.POINT_LISTS[round_number]

    CONTROL_CORRECT_ANSWERS = {
        'A': 50,
        'B': cu(450),
    }


class Subsession(BaseSubsession):
    exp_num = models.IntegerField()


def creating_session(subsession):
    set_groups(subsession)
    set_counters(subsession)


class Group(BaseGroup):

    def set_payoffs(self):
        for player in self.get_players():
            selected_situation = random.randint(0, 20)
            player.selected_situation = selected_situation
            selected_risk_field = f'R{selected_situation}'
            decision = getattr(player, selected_risk_field)

            if decision == 'L':
                lottery = random.choice(['won', 'lost'])
                if lottery == 'won':
                    player.lottery_won = True
                    amount = 1000

                elif lottery == 'lost':
                    player.lottery_won = False
                    amount = 0

            elif decision == 'S':
                point_list = C.get_point_list(self.round_number)
                amount = point_list[selected_situation]

            player.payoff = cu(amount)


def make_risk_field(label=None):
    label = label or ''
    return models.StringField(
        choices=[
            ['L', 'Lottery'],
            ['S', 'Sure payment'],
        ],
        label=label,
        widget=widgets.RadioSelectHorizontal()
    )


class Player(BasePlayer, ControlPlayerMixin):
    CP1_A = models.IntegerField(min=0, max=100, help_text='percent')
    CP1_B = models.CurrencyField(min=0, max=1000)
    CP2_A = models.IntegerField(min=0, max=100, help_text='percent')
    CP2_B = models.CurrencyField(min=0, max=1000)

    selected_situation = models.IntegerField()
    lottery_won = models.BooleanField()

    s_cursor = models.IntegerField(initial=0)

    R0 = make_risk_field()
    R1 = make_risk_field()
    R2 = make_risk_field()
    R3 = make_risk_field()
    R4 = make_risk_field()
    R5 = make_risk_field()
    R6 = make_risk_field()
    R7 = make_risk_field()
    R8 = make_risk_field()
    R9 = make_risk_field()
    R10 = make_risk_field()
    R11 = make_risk_field()
    R12 = make_risk_field()
    R13 = make_risk_field()
    R14 = make_risk_field()
    R15 = make_risk_field()
    R16 = make_risk_field()
    R17 = make_risk_field()
    R18 = make_risk_field()
    R19 = make_risk_field()
    R20 = make_risk_field()

    @property
    def current_sure_price(self):
        return C.get_point_list(self.round_number)[self.s_cursor]



# PAGES
class Instructions_1(Page):

    @staticmethod
    def vars_for_template(player):
        return {'round_number': player.round_number}


class Control(ControlPage):
    pass


class ControlFailed(ControlFailedPage):
    pass


class Instructions_2(Page):

    @staticmethod
    def vars_for_template(player):
        return {'point_list': C.get_point_list(player.round_number)}


page_sequence = [
    ExpPaymentAlert,
    Instructions_1,
    Control,
    Control,
    ControlFailed,
    ControlPassed,
    Instructions_2,
    SimpleWaitPage,
    *[RiskDecision] * len(C.get_point_list(1)),
    PayoffWaitPage,
]
