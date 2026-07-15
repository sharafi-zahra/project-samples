from otree.api import *

from settings import SURVEY_CURRENCY as currency
from core import (
    SliderField,
    SurveyPaymentAlert,
    SurveyPage,
    EndingSurveyWaitPage,
    set_counters,
)


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'survey_time'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    TODAY_FIXED_PRICE = f'{100.0} {currency}'
    DATED_PRICES = [
        f'{100.0} {currency}',
        f'{103.0} {currency}',
        f'{106.1} {currency}',
        f'{109.2} {currency}',
        f'{112.4} {currency}',
        f'{115.6} {currency}',
        f'{118.8} {currency}',
        f'{122.1} {currency}',
        f'{125.4} {currency}',
        f'{128.8} {currency}',
        f'{132.3} {currency}',
        f'{135.7} {currency}',
        f'{139.2} {currency}',
        f'{142.8} {currency}',
        f'{146.4} {currency}',
        f'{150.1} {currency}',
        f'{153.8} {currency}',
        f'{157.5} {currency}',
        f'{161.3} {currency}',
        f'{165.1} {currency}',
        f'{169.0} {currency}',
        f'{172.9} {currency}',
        f'{176.9} {currency}',
        f'{180.9} {currency}',
        f'{185.0} {currency}',
    ]

    LADDER_PRICES_ROADMAP = {
        106: {'increase': 109, 'decrease': 103},
        112: {'increase': 119, 'decrease': 106},
        119: {'increase': 122, 'decrease': 116},
        125: {'increase': 139, 'decrease': 112},
        132: {'increase': 136, 'decrease': 129},
        139: {'increase': 146, 'decrease': 132},
        146: {'increase': 150, 'decrease': 143},
        154: {'increase': 185, 'decrease': 125},
        161: {'increase': 165, 'decrease': 158},
        169: {'increase': 177, 'decrease': 161},
        177: {'increase': 181, 'decrease': 173},
        185: {'increase': 202, 'decrease': 169},
        193: {'increase': 197, 'decrease': 189},
        202: {'increase': 210, 'decrease': 193},
        210: {'increase': 216, 'decrease': 206},
    }

    LABEL_PAIRS = [
        dict(
            least='Completely unwilling to do so',
            most='Very willing to do so',
        ),
        dict(
            least='Not willing to do so',
            most='Very willing to do so',
        ),
        dict(
            least='Does not describe me at all',
            most='Describes me perfectly',
        ),
        dict(
            least='Does not apply at all',
            most='Applies fully',
        ),
        dict(
            least='You cannot rely on my answers',
            most='You can rely on my answers',
        ),
    ]
    SLIDER_LABELS = {
        "P1_Q1": LABEL_PAIRS[0],
        "P2_Q1": LABEL_PAIRS[0],
        "P3_Q1": LABEL_PAIRS[0],
        ############################
        "P4_Q1": LABEL_PAIRS[1],
        "P4_Q2": LABEL_PAIRS[1],
        "P4_Q3": LABEL_PAIRS[1],
        "P4_Q4": LABEL_PAIRS[1],
        "P4_Q5": LABEL_PAIRS[1],
        ############################
        "P5_Q1": LABEL_PAIRS[2],
        ############################
        "P7_Q1": LABEL_PAIRS[3],
        "P7_Q2": LABEL_PAIRS[3],
        "P7_Q3": LABEL_PAIRS[3],
        "P7_Q4": LABEL_PAIRS[3],
        "P7_Q5": LABEL_PAIRS[3],
        ############################
        "P9_Q1": LABEL_PAIRS[4],
    }


class Subsession(BaseSubsession):
    survey_num = models.IntegerField()


def creating_session(subsession):
    set_counters(subsession)


class Group(BaseGroup):
    pass


def make_time_field(label=None):
    label = label or ''
    return models.IntegerField(
        label=label,
        choices=[
            [0, 'Today'],
            [12, 'In 12 months'],
        ],
        widget=widgets.RadioSelectHorizontal()
    )


class Player(BasePlayer):
    L1_decision = make_time_field()
    L1_amount = models.CurrencyField(initial=cu(154))
    L2_decision = make_time_field()
    L2_amount = models.CurrencyField()
    L3_decision = make_time_field()
    L3_amount = models.CurrencyField()
    L4_decision = make_time_field()
    L4_amount = models.CurrencyField()
    L5_decision = make_time_field()
    L5_amount = models.CurrencyField()

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


    P1_Q1 = SliderField()
    P2_Q1 = SliderField()
    P3_Q1 = SliderField()

    P4_Q1 = SliderField(label='When it comes to financial investments?')
    P4_Q2 = SliderField(label='When it comes to important decisions in life?')
    P4_Q3 = SliderField(label='When it comes to your professional career?')
    P4_Q4 = SliderField(label='When it comes to bigger purchases?')
    P4_Q5 = SliderField(label='When it comes to a longer journey/trip?')

    P5_Q1 = SliderField()

    P6_Q1 = models.IntegerField(
        label='''
            Please consider: how many extra days would one have to offer you for
            you to be willing to postpone the trip for three years?
        ''',
        help_text='days',
        min=0,
        max=1000000000,
    )
    P6_Q2 = models.CurrencyField(
        label='''
            If it was possible to exchange the trip for money: how much money would
            one need to offer you for you to be willing to forgo the trip?
        ''',
        min=0,
        max=1000000000,
    )

    P7_Q1 = SliderField(label='I try hard to always have some extra money for unexpected expenditures.')
    P7_Q2 = SliderField(label='I give up something today so that I can afford more tomorrow.')
    P7_Q3 = SliderField(label='I would rather have some fun today and not think about tomorrow.')
    P7_Q4 = SliderField(label='My monthly expenses often exceed what I can afford.')
    P7_Q5 = SliderField(label='I am a person who often does not keep their own good resolutions.')

    P8_Q1 = models.CurrencyField(
        label='Please try to specify the amount you save per month as exactly as possible.',
        min=0,
        max=1000000000,
    )

    P9_Q1 = SliderField()



# PAGES
class SliderLabelsMixin:

    @property
    def slider_labels(self):
        return {
            field: label_pair
            for field, label_pair in C.SLIDER_LABELS.items()
            if field.startswith(f"P{self.page_number()}_")
        }


class Instructions_1(Page):
    pass


class Ladder(Page):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player):
        for i in range(1, 6):
            if player.field_maybe_none(f'L{i}_decision') is None:
                return [f'L{i}_decision']

    @staticmethod
    def vars_for_template(player):
        for i in range(1, 6):
            if player.field_maybe_none(f'L{i}_decision') is None:
                amount = float(player.field_maybe_none(f'L{i}_amount'))
                return {
                    'dated_price': f'{amount} {currency}',
                }

    @staticmethod
    def before_next_page(player, timeout_happened):
        for i in range(4, 0, -1):
            recent_decision = player.field_maybe_none(f'L{i}_decision')
            if recent_decision is not None:
                recent_amount = player.field_maybe_none(f'L{i}_amount')
                if recent_decision == 0:
                    next_amount = C.LADDER_PRICES_ROADMAP[recent_amount]['increase']

                elif recent_decision == 12:
                    next_amount = C.LADDER_PRICES_ROADMAP[recent_amount]['decrease']

                else:
                    raise Exception(f'invalid value for "L{i}_decision" field: {recent_decision}')

                setattr(player, f'L{i+1}_amount', next_amount)
                break


class Instructions_2(Page):
    pass


class Instructions_3(Page):

    @staticmethod
    def vars_for_template(player):
        return {
            'dated_prices': C.DATED_PRICES,
        }


class Decision(Page):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player):
        situation = player.s_cursor
        return [f'T{situation}']

    @staticmethod
    def vars_for_template(player):
        return {
            'situation': player.s_cursor + 1,
            'dated_price': C.DATED_PRICES[player.s_cursor],
        }

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.s_cursor += 1


class QuestionPage_1(SurveyPage, SliderLabelsMixin):
    pass


class QuestionPage_2(SurveyPage, SliderLabelsMixin):
    pass


class QuestionPage_3(SurveyPage, SliderLabelsMixin):
    pass


class QuestionPage_4(SurveyPage, SliderLabelsMixin):
    pass


class QuestionPage_5(SurveyPage, SliderLabelsMixin):
    pass


class QuestionPage_6(SurveyPage, SliderLabelsMixin):
    pass


class QuestionPage_7(SurveyPage, SliderLabelsMixin):
    pass


class QuestionPage_8(SurveyPage, SliderLabelsMixin):
    pass


class QuestionPage_9(SurveyPage, SliderLabelsMixin):
    pass



page_sequence = [
    SurveyPaymentAlert,
    Instructions_1,
    *[Ladder] * 5,
    Instructions_2,
    Instructions_3,
    *[Decision] * len(C.DATED_PRICES),
    QuestionPage_1,
    QuestionPage_2,
    QuestionPage_3,
    QuestionPage_4,
    QuestionPage_5,
    QuestionPage_6,
    QuestionPage_7,
    QuestionPage_8,
    QuestionPage_9,
    EndingSurveyWaitPage,
]
