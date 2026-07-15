from otree.api import *

from settings import SURVEY_CURRENCY as currency
from core import (
    SliderField,
    SurveyPaymentAlert,
    SurveyPage,
    RiskDecision,
    EndingSurveyWaitPage,
    set_counters,
    LotteryPrize,
)


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'survey_risk'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    LOTTERY_PRIZE = LotteryPrize(
        f'{300} {currency}',
        f'{0} {currency}'
    )
    SURE_PRICES = {
        1: [f'{price} {currency}' for price in range(0, 301, 10)],
    }

    LADDER_PRICES_ROADMAP = {
        20: {'increase': 30, 'decrease': 10},
        40: {'increase': 60, 'decrease': 20},
        60: {'increase': 70, 'decrease': 50},
        80: {'increase': 120, 'decrease': 40},
        100: {'increase': 110, 'decrease': 90},
        120: {'increase': 140, 'decrease': 100},
        140: {'increase': 150, 'decrease': 130},
        160: {'increase': 240, 'decrease': 80},
        180: {'increase': 190, 'decrease': 170},
        200: {'increase': 220, 'decrease': 180},
        220: {'increase': 230, 'decrease': 210},
        240: {'increase': 280, 'decrease': 200},
        260: {'increase': 270, 'decrease': 250},
        280: {'increase': 300, 'decrease': 260},
        300: {'increase': 310, 'decrease': 290},
    }

    LABEL_PAIRS = [
        dict(
            least='Completely unwilling to take risks',
            most='Very willing to take risks',
        ),
        dict(
            least='Not willing to take risks at all',
            most='Very willing to take risks',
        ),
        dict(
            least='Completely unsure',
            most='Very sure',
        ),
        dict(
            least='Very unlikely',
            most='Very likely',
        ),
        dict(
            least='Does not apply at all',
            most='Applies fully',
        ),
    ]
    SLIDER_LABELS = {
        "P1_Q1": LABEL_PAIRS[0],
        "P2_Q1": LABEL_PAIRS[0],
        "P3_Q1": LABEL_PAIRS[0],
        "P4_Q1": LABEL_PAIRS[2],
        ############################
        "P5_Q1": LABEL_PAIRS[1],
        "P5_Q2": LABEL_PAIRS[1],
        "P5_Q3": LABEL_PAIRS[1],
        "P5_Q4": LABEL_PAIRS[1],
        "P5_Q5": LABEL_PAIRS[1],
        "P5_Q6": LABEL_PAIRS[1],
        ############################
        "P6_Q1": LABEL_PAIRS[3],
        ############################
        "P7_Q1": LABEL_PAIRS[4],
        "P7_Q2": LABEL_PAIRS[4],
        "P7_Q3": LABEL_PAIRS[4],
    }

    @classmethod
    def get_sure_prices(cls, round_number):
        return cls.SURE_PRICES[round_number]


class Subsession(BaseSubsession):
    survey_num = models.IntegerField()


def creating_session(subsession):
    set_counters(subsession)


class Group(BaseGroup):
    pass


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


class Player(BasePlayer):
    L1_decision = make_risk_field()
    L1_amount = models.CurrencyField(initial=cu(160))
    L2_decision = make_risk_field()
    L2_amount = models.CurrencyField()
    L3_decision = make_risk_field()
    L3_amount = models.CurrencyField()
    L4_decision = make_risk_field()
    L4_amount = models.CurrencyField()
    L5_decision = make_risk_field()
    L5_amount = models.CurrencyField()

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
    R21 = make_risk_field()
    R22 = make_risk_field()
    R23 = make_risk_field()
    R24 = make_risk_field()
    R25 = make_risk_field()
    R26 = make_risk_field()
    R27 = make_risk_field()
    R28 = make_risk_field()
    R29 = make_risk_field()
    R30 = make_risk_field()

    P1_Q1 = SliderField()
    P2_Q1 = SliderField()
    P3_Q1 = SliderField()
    P4_Q1 = SliderField()

    P5_Q1 = SliderField(label='When it comes to financial investments?')
    P5_Q2 = SliderField(label='When it comes to important decisions in life?')
    P5_Q3 = SliderField(label='When it comes to your professional career?')
    P5_Q4 = SliderField(label='When it comes to leisure and sports?')
    P5_Q5 = SliderField(label='When it comes to behavior in road traffic?')
    P5_Q6 = SliderField(label='When it comes to dealing with other people?')

    P6_Q1 = SliderField()

    P7_Q1 = SliderField(label='I often behave according to the motto: It is better to be safe than sorry.')
    P7_Q2 = SliderField(label='I avoid risky things.')
    P7_Q3 = SliderField(label='I like taking risks.')

    P8_Q1 = models.CurrencyField(
        label='We would like to know: How much of the money you won in the lottery would you invest in the risky yet profitable lottery?',
        choices=[
            [100000, f'The whole amount of 100.000 {currency}'],
            [80000, f'80.000 {currency}'],
            [60000, f'60.000 {currency}'],
            [40000, f'40.000 {currency}'],
            [20000, f'20.000 {currency}'],
            [0, f'Nothing at all'],
        ],
        widget=widgets.RadioSelect,
    )

    @property
    def current_sure_price(self):
        return C.get_sure_prices(self.round_number)[self.s_cursor]



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
                amount = int(player.field_maybe_none(f'L{i}_amount'))
                return {
                    'sure_price': f"{amount} {currency}",
                }

    @staticmethod
    def before_next_page(player, timeout_happened):
        for i in range(4, 0, -1):
            recent_decision = player.field_maybe_none(f'L{i}_decision')
            if recent_decision is not None:
                recent_amount = player.field_maybe_none(f'L{i}_amount')
                if recent_decision == 'L':
                    next_amount = C.LADDER_PRICES_ROADMAP[recent_amount]['increase']

                elif recent_decision == 'S':
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
        return {'sure_prices': C.get_sure_prices(player.round_number)}


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



page_sequence = [
    SurveyPaymentAlert,
    Instructions_1,
    *[Ladder] * 5,
    Instructions_2,
    Instructions_3,
    *[RiskDecision] * len(C.SURE_PRICES[1]),
    QuestionPage_1,
    QuestionPage_2,
    QuestionPage_3,
    QuestionPage_4,
    QuestionPage_5,
    QuestionPage_6,
    QuestionPage_7,
    QuestionPage_8,
    EndingSurveyWaitPage,
]
