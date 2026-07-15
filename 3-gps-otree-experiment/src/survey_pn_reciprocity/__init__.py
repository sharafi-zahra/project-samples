from otree.api import *

from settings import SURVEY_CURRENCY as currency
from core import (
    SliderField,
    SurveyPage,
    set_counters,
)


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'survey_pn_reciprocity'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    LABEL_PAIRS = [
        dict(
            least='Not willing to do so',
            most='Very willing to do so',
        ),
        dict(
            least='Completely unwilling to do so',
            most='Very willing to do so',
        ),
        dict(
            least='Does not describe me at all',
            most='Describes me perfectly',
        ),
        dict(
            least='Absolutely unfair',
            most='Absolutely fair',
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

        "P4_Q1": LABEL_PAIRS[0],
        "P4_Q2": LABEL_PAIRS[0],
        "P4_Q3": LABEL_PAIRS[0],
        "P4_Q4": LABEL_PAIRS[0],
        "P4_Q5": LABEL_PAIRS[0],

        "P5_Q1": LABEL_PAIRS[1],
        "P6_Q1": LABEL_PAIRS[1],
        "P7_Q1": LABEL_PAIRS[1],
        "P8_Q1": LABEL_PAIRS[1],

        "P9_Q1": LABEL_PAIRS[1],
        "P9_Q2": LABEL_PAIRS[1],
        "P9_Q3": LABEL_PAIRS[1],
        "P9_Q4": LABEL_PAIRS[1],
        "P9_Q5": LABEL_PAIRS[1],

        "P14_Q1": LABEL_PAIRS[2],
        "P14_Q2": LABEL_PAIRS[2],
        "P14_Q3": LABEL_PAIRS[2],
        "P14_Q4": LABEL_PAIRS[2],
        "P14_Q5": LABEL_PAIRS[2],
        "P14_Q6": LABEL_PAIRS[2],
        "P14_Q7": LABEL_PAIRS[2],
        "P14_Q8": LABEL_PAIRS[2],
        "P14_Q9": LABEL_PAIRS[2],

        "P15_Q1": LABEL_PAIRS[2],
        "P15_Q2": LABEL_PAIRS[2],
        "P15_Q3": LABEL_PAIRS[2],
        "P15_Q4": LABEL_PAIRS[2],
        "P15_Q5": LABEL_PAIRS[2],
        "P15_Q6": LABEL_PAIRS[2],
        "P15_Q7": LABEL_PAIRS[2],

        "P16_Q1": LABEL_PAIRS[3],

        "P17_Q1": LABEL_PAIRS[4],
    }


class Subsession(BaseSubsession):
    survey_num = models.IntegerField()


def creating_session(subsession):
    set_counters(subsession)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    P1_Q1 = SliderField()
    P2_Q1 = SliderField()
    P3_Q1 = SliderField()

    P4_Q1 = SliderField(label="When it comes to people in your hometown.")
    P4_Q2 = SliderField(label="When it comes to your circle of friends.")
    P4_Q3 = SliderField(label="When it comes to your professional environment.")
    P4_Q4 = SliderField(label="When it comes to strangers.")
    P4_Q5 = SliderField(label="When it comes to people in your neighborhood.")

    P5_Q1 = SliderField()
    P6_Q1 = SliderField()
    P7_Q1 = SliderField()
    P8_Q1 = SliderField()

    P9_Q1 = SliderField(label="When it comes to people in your hometown.")
    P9_Q2 = SliderField(label="When it comes to your circle of friends.")
    P9_Q3 = SliderField(label="When it comes to your professional environment.")
    P9_Q4 = SliderField(label="When it comes to strangers.")
    P9_Q5 = SliderField(label="When it comes to people in your neighborhood.")

    P10_Q1 = models.CurrencyField(
        label="Assume that the other person makes the proposal about how to divide the money. You, on the other hand, have to decide whether to accept or reject the proposal. What is the minimum amount the other person has to offer you for you to be willing to accept the proposal?",
        min=0,
        max=100,
    )
    P10_Q2 = models.CurrencyField(
        label="Assume that you have to make the proposal about how to divide the money. Which amount would you offer to the other person? ",
        min=0,
        max=100,
    )

    P11_Q1 = models.StringField(
        label="Do you give one of the presents to the stranger as a “thank you” gift?",
        choices=[
            f"I don't give a gift",
            f'I give the gift that worth 5 {currency}.',
            f'I give the gift that worth 10 {currency}.',
            f'I give the gift that worth 15 {currency}.',
            f'I give the gift that worth 20 {currency}.',
            f'I give the gift that worth 25 {currency}.',
            f'I give the gift that worth 30 {currency}.',
        ],
        widget=widgets.RadioSelect,
    )
    P12_Q1 = models.StringField(
        label="How much do you spend on a present that you then send to the stranger?",
        choices = [
            f"I don't send a present at all.",
            f"I send a present for 5 {currency}.",
            f"I send a present for 20 {currency}.",
            f"I send a present for 50 {currency}.",
            f"I send a present for 100 {currency}.",
            f"I send a present for 120 {currency}.",
            f"I send a present for 150 {currency}.",
            f"I send a present for more than 150 {currency}."
        ],
        widget=widgets.RadioSelect,
    )

    P13_Q1 = models.CurrencyField(
        label=f"Assume that the other person transfers 5 {currency} to your account. After the first step you have 20+3*5 {currency} = 35 {currency}, the other person has 20-5 {currency} = 15 {currency}. Which amount do you transfer back?",
        min=0,
        max=35,
    )
    P13_Q2 = models.CurrencyField(
        label=f"Assume that the other person transfers 10 {currency} to your account. After the first step you have 20+3*10 {currency} = 50 {currency}, the other person has 20-10 {currency} = 10 {currency}. Which amount do you transfer back?",
        min=0,
        max=50,
    )
    P13_Q3 = models.CurrencyField(
        label=f"Assume that the other person transfers 15 {currency} to your account. After the first step you have 20+3*15 {currency} = 65 {currency}, the other person has 20-15 {currency} = 5 {currency}. Which amount do you transfer back?",
        min=0,
        max=65,
    )
    P13_Q4 = models.CurrencyField(
        label=f"Assume that the other person transfers 20 {currency} to your account. After the first step, you have 20+3*20 {currency} = 80 {currency}, the other person has 20-20 {currency} = 0 {currency}. Which amount do you transfer back?",
        min=0,
        max=80,
    )
    P13_Q5 = models.CurrencyField(
        label=f"Finally, a different question: assume you were in the position of the other person and had to decide which amount to transfer. Which amount would you transfer?",
        min=0,
        max=20,
    )

    P14_Q1 = SliderField(label="When someone does me a favor, I am willing to return it.")
    P14_Q2 = SliderField(label="If I am treated very unjustly, I will take revenge at the first occasion, even if there is a cost to do so.")
    P14_Q3 = SliderField(label="When someone puts me into a difficult situation I will do the same to them.")
    P14_Q4 = SliderField(label="I go out of my way to help someone who has helped me before.")
    P14_Q5 = SliderField(label="If someone insults me I will also behave in an insulting way towards them.")
    P14_Q6 = SliderField(label="I am willing to incur costs to help someone who has helped me before.")
    P14_Q7 = SliderField(label="If someone harms me on purpose I will try to give that person a taste of their own medicine.")
    P14_Q8 = SliderField(label="I am not a person who is taken for a fool.")
    P14_Q9 = SliderField(label="I do not like the feeling of owing something to someone.")

    P15_Q1 = SliderField(label="If someone behaves unfairly towards me in sports, I will also behave unfairly towards them.")
    P15_Q2 = SliderField(label="I am not a person who lets others push me around.")
    P15_Q3 = SliderField(label="If a colleague does me a favor at work, I make sure to return the favor at the next occasion, even if I have to invest precious time to do so.")
    P15_Q4 = SliderField(label="When someone treats me in a bad way, I do not just let it go.")
    P15_Q5 = SliderField(label="I absolutely dislike being the fool.")
    P15_Q6 = SliderField(label="It is important to me to be respected by others.")
    P15_Q7 = SliderField(label="You sometimes have to play tough in order not to be taken advantage of.")

    P16_Q1 = SliderField()

    P17_Q1 = SliderField()


# PAGES
class SliderLabelsMixin:

    @property
    def slider_labels(self):
        return {
            field: label_pair
            for field, label_pair in C.SLIDER_LABELS.items()
            if field.startswith(f"P{self.page_number()}_")
        }


class Instructions(Page):
    pass


class Page_1(SurveyPage, SliderLabelsMixin):
    pass


class Page_2(SurveyPage, SliderLabelsMixin):
    pass


class Page_3(SurveyPage, SliderLabelsMixin):
    pass


class Page_4(SurveyPage, SliderLabelsMixin):
    pass


class Page_5(SurveyPage, SliderLabelsMixin):
    pass


class Page_6(SurveyPage, SliderLabelsMixin):
    pass


class Page_7(SurveyPage, SliderLabelsMixin):
    pass


class Page_8(SurveyPage, SliderLabelsMixin):
    pass


class Page_9(SurveyPage, SliderLabelsMixin):
    pass


class Page_10(SurveyPage, SliderLabelsMixin):
    pass


class Page_11(SurveyPage, SliderLabelsMixin):
    pass


class Page_12(SurveyPage, SliderLabelsMixin):
    pass


class Page_13(SurveyPage, SliderLabelsMixin):
    pass


class Page_14(SurveyPage, SliderLabelsMixin):
    pass


class Page_15(SurveyPage, SliderLabelsMixin):
    pass


class Page_16(SurveyPage, SliderLabelsMixin):
    pass


class Page_17(SurveyPage, SliderLabelsMixin):
    pass


page_sequence = [
    Instructions,
    Page_1,
    Page_2,
    Page_3,
    Page_4,
    Page_5,
    Page_6,
    Page_7,
    Page_8,
    Page_9,
    Page_10,
    Page_11,
    Page_12,
    Page_13,
    Page_14,
    Page_15,
    Page_16,
    Page_17,
]
