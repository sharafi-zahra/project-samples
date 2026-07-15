import random

from otree.api import *
from otree.i18n import core_gettext

from core import (
    ExpPaymentAlert,
    ControlPage,
    ControlFailedPage,
    ControlPlayerMixin,
    ControlPassed,
    SimpleWaitPage,
    PayoffWaitPage,
    set_counters,
)


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'exp_time'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 2

    CURRENCY = core_gettext('points')

    ROUND_ORDER = {
        'player_0': ['0-12__1', '0-12__2'],
        'player_1': ['0-12__1', '0-12__2'],
    }

    CONDITIONS_INFO = {
        '0-12__1': {
            'choices': [
                [0, 'Today'],
                [12, 'In 12 Months']
            ],
            'point_list_1': [1600.0] * 25,
            'point_list_2': [1600, 1648.4, 1697.4, 1747.2, 1797.8, 1849.0, 1901.0, 1953.6, 2007.0, 2061.2, 2116.0, 2171.6, 2227.8, 2284.8, 2342.6, 2401.0, 2460.2, 2520.0, 2580.6, 2642.0, 2704.0, 2766.8, 2830.2, 2894.4, 2959.4]
        },

        '0-12__2': {
            'choices': [
                [0, 'Today'],
                [12, 'In 12 Months']
            ],
            'point_list_1': [1600.0] * 25,
            'point_list_2': [1600.0, 1651.0, 1688.5, 1755.6, 1800.5, 1853.4, 1910.9, 1954.7, 2007.7, 2063.8, 2106.7, 2168.7, 2233.6, 2283.2, 2345.8, 2393.2, 2467.2, 2523.8, 2573.0, 2632.6, 2712.4, 2772.3, 2839.2, 2899.3, 2961.9]
        },
    }

    CONTROL_CORRECT_ANSWERS = {
        'A': 1600,
        'B': 1747.2,
    }


class Subsession(BaseSubsession):
    exp_num = models.IntegerField()


def creating_session(subsession):
    set_counters(subsession)


class Group(BaseGroup):

    def set_payoffs(self):
        for player in self.get_players():
            selected_situation = random.randint(0, 24)
            player.selected_situation = selected_situation
            selected_decision = 'T{}'.format(selected_situation)
            decision = getattr(player, selected_decision)
            condition = player.condition

            choice_1 = C.CONDITIONS_INFO[condition]['choices'][0][0]
            choice_2 = C.CONDITIONS_INFO[condition]['choices'][1][0]

            if decision == choice_1:
                amount = C.CONDITIONS_INFO[condition]['point_list_1'][selected_situation]

            elif decision == choice_2:
                amount = C.CONDITIONS_INFO[condition]['point_list_2'][selected_situation]

            player.dated_payoff = cu(amount)
            player.payoff_date = decision
            payment_info = {
                'round_number': self.round_number,
                'condition': condition,
                'amount': player.dated_payoff,
                'date': player.payoff_date
            }

            if self.round_number == 1:
                player.participant.exp_time_payoff = []

            player.participant.exp_time_payoff.append(payment_info)


def make_time_field(label=None):
    label = label or ''
    return models.IntegerField(
        label=label,
        widget=widgets.RadioSelectHorizontal()
    )


class Player(BasePlayer, ControlPlayerMixin):
    CP1_A = models.FloatField(min=0, max=10000, help_text=C.CURRENCY)
    CP1_B = models.FloatField(min=0, max=10000, help_text=C.CURRENCY)
    CP2_A = models.FloatField(min=0, max=10000, help_text=C.CURRENCY)
    CP2_B = models.FloatField(min=0, max=10000, help_text=C.CURRENCY)

    condition = models.StringField()
    selected_situation = models.IntegerField()

    s_cursor = models.IntegerField(initial=0)

    T0 = make_time_field()
    T1 = make_time_field()
    T2 = make_time_field()
    T3 = make_time_field()
    T4 = make_time_field()
    T5 = make_time_field()
    T6 = make_time_field()
    T7 = make_time_field()
    T8 = make_time_field()
    T9 = make_time_field()
    T10 = make_time_field()
    T11 = make_time_field()
    T12 = make_time_field()
    T13 = make_time_field()
    T14 = make_time_field()
    T15 = make_time_field()
    T16 = make_time_field()
    T17 = make_time_field()
    T18 = make_time_field()
    T19 = make_time_field()
    T20 = make_time_field()
    T21 = make_time_field()
    T22 = make_time_field()
    T23 = make_time_field()
    T24 = make_time_field()

    dated_payoff = models.CurrencyField(min=0)
    payoff_date = models.IntegerField(min=0)


def make_choices_list(player_id_in_group, round_number):
    player_number = 'player_{}'.format(player_id_in_group % 2)
    current_condition = C.ROUND_ORDER[player_number][round_number - 1]
    return C.CONDITIONS_INFO[current_condition]['choices']


def T0_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T1_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T2_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T3_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T4_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T5_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T6_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T7_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T8_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T9_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T10_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T11_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T12_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T13_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T14_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T15_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T16_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T17_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T18_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T19_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T20_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T21_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T22_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T23_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)

def T24_choices(player):
    return make_choices_list(player.id_in_group, player.round_number)


# PAGES
class Instructions_1(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class Control(ControlPage):
    pass


class ControlFailed(ControlFailedPage):
    pass


class Instructions_2(Page):

    @staticmethod
    def vars_for_template(player):
        current_condition = C.ROUND_ORDER[f'player_{(player.id_in_group % 2)}'][player.round_number - 1]
        player.condition = current_condition
        return {'current_condition': current_condition}


class Instructions_3(Page):

    @staticmethod
    def vars_for_template(player):
        current_condition = player.condition
        point_list_1 = C.CONDITIONS_INFO[current_condition]['point_list_1']
        point_list_2 = C.CONDITIONS_INFO[current_condition]['point_list_2']

        return dict(
            current_condition=current_condition,
            counter_list=[x for x in range(0, 25)],
            point_lists=zip(point_list_1, point_list_2),
            currency=C.CURRENCY,
        )


class Decision(Page):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player):
        situation = player.s_cursor
        return [f'T{situation}']

    @staticmethod
    def vars_for_template(player):
        current_condition = player.condition
        situation = player.s_cursor
        point_list_1 = C.CONDITIONS_INFO[current_condition]['point_list_1']
        point_list_2 = C.CONDITIONS_INFO[current_condition]['point_list_2']

        return dict(
            current_condition=current_condition,
            situation=situation + 1,
            point_1=point_list_1[situation],
            point_2=point_list_2[situation],
            currency=C.CURRENCY,
        )

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.s_cursor += 1


page_sequence = [
    ExpPaymentAlert,
    Instructions_1,
    Control,
    Control,
    ControlFailed,
    ControlPassed,
    Instructions_2,
    Instructions_3,
    SimpleWaitPage,
    *[Decision] * 25,
    PayoffWaitPage,
]
