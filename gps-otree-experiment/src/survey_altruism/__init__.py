from otree.api import *

from settings import SURVEY_CURRENCY as currency
from core import (
    SliderField,
    SurveyPaymentAlert,
    SurveyPage,
    set_counters,
)


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'survey_altruism'
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
            least='You cannot rely on my answers',
            most='You can rely on my answers',
        ),
    ]
    SLIDER_LABELS = {
        "P1_Q1": LABEL_PAIRS[0],
        "P2_Q1": LABEL_PAIRS[0],
        "P3_Q1": LABEL_PAIRS[0],
        ##################################################
        "P4_Q1": LABEL_PAIRS[1],
        "P4_Q2": LABEL_PAIRS[1],
        "P4_Q3": LABEL_PAIRS[1],
        "P4_Q4": LABEL_PAIRS[1],
        "P4_Q5": LABEL_PAIRS[1],
        "P4_Q6": LABEL_PAIRS[1],
        "P4_Q7": LABEL_PAIRS[1],
        ##################################################
        "P6_Q01": LABEL_PAIRS[2],
        "P6_Q02": LABEL_PAIRS[2],
        "P6_Q03": LABEL_PAIRS[2],
        "P6_Q04": LABEL_PAIRS[2],
        "P6_Q05": LABEL_PAIRS[2],
        "P6_Q06": LABEL_PAIRS[2],
        "P6_Q07": LABEL_PAIRS[2],
        "P6_Q08": LABEL_PAIRS[2],
        "P6_Q09": LABEL_PAIRS[2],
        "P6_Q10": LABEL_PAIRS[2],
        ##################################################
        "P9_Q1": LABEL_PAIRS[3],
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

    P4_Q1 = SliderField(label="With people in your hometown?")
    P4_Q2 = SliderField(label="With people in your circle of friends?")
    P4_Q3 = SliderField(label="With people from your professional environment?")
    P4_Q4 = SliderField(label="With strangers?")
    P4_Q5 = SliderField(label="With people in your neighborhood?")
    P4_Q6 = SliderField(label="With people in distress or emergency situations?")
    P4_Q7 = SliderField(label="When it comes to good causes?")

    P5_Q1 = models.CurrencyField(
        label=f"Today you unexpectedly received <b>1,000 {currency}</b>. How much of this amount would you donate to a good cause?",
        # widget=widgets.NumberInput,
        help_text="<b>values between 0 and 1000 are allowed</b>",
        # verbose_name="<b>(values between 0 and 1000 are allowed)</b>",
        min=0,
        max=1000,
    )

    P6_Q01 = SliderField(label="At work, I am only willing to do something for a colleague if I expect that they would do the same for me.")
    P6_Q02 = SliderField(label="I am willing to donate time and money to charity, even if I do not profit from that directly.")
    P6_Q03 = SliderField(label="I am willing to help others even if I expect that I will never meet them again.")
    P6_Q04 = SliderField(label="When I spend time and money on something I expect to profit from that in the future.")
    P6_Q05 = SliderField(label="When I donate money I expect that this is recognized and acknowledged.")
    P6_Q06 = SliderField(label="I do not understand why some people spend their lifetime fighting for a cause which they do not benefit from directly.")
    P6_Q07 = SliderField(label="I am a person who would give their shirt off their back to help others.")
    P6_Q08 = SliderField(label="In comparison to others I am a rather selfless person.")
    P6_Q09 = SliderField(label="I am only willing to help others if I expect that they would do the same for me.")
    P6_Q10 = SliderField(label="Other people regard me as an unselfish person.")

    P7_Q1 = models.IntegerField(
        label="Please specify as precisely as possible how many hours per month you volunteer for good causes, e.g. protecting the environment, youth work, etc.",
        help_text="hours",
        min=0,
        max=1000,
    )
    P8_Q1 = models.IntegerField(
        label="How many people know that you commit time to charitable purposes?",
        help_text="persons",
        min=0,
        max=1000,
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


page_sequence = [
    SurveyPaymentAlert,
    Page_1,
    Page_2,
    Page_3,
    Page_4,
    Page_5,
    Page_6,
    Page_7,
    Page_8,
    Page_9,
]
