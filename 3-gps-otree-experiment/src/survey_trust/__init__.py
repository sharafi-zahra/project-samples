from otree.api import *

from core import SliderField, SurveyPaymentAlert, SurveyPage, set_counters


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'survey_trust'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    LABEL_PAIRS = [
        dict(
            least='Not willing to trust at all',
            most='Very willing to trust',
        ),
        dict(
            least='Never',
            most='Very often',
        ),
        dict(
            least='Does not describe me at all',
            most='Describes me perfectly',
        ),
        dict(
            least='Doesn\'t apply at all',
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

        "P4_Q1": LABEL_PAIRS[0],
        "P4_Q2": LABEL_PAIRS[0],
        "P4_Q3": LABEL_PAIRS[0],
        "P4_Q4": LABEL_PAIRS[0],
        "P4_Q5": LABEL_PAIRS[0],

        "P6_Q1": LABEL_PAIRS[1],
        "P6_Q2": LABEL_PAIRS[1],
        "P6_Q3": LABEL_PAIRS[1],

        "P7_Q1": LABEL_PAIRS[2],
        "P7_Q2": LABEL_PAIRS[2],
        "P7_Q3": LABEL_PAIRS[2],
        "P7_Q4": LABEL_PAIRS[2],

        "P8_Q1": LABEL_PAIRS[3],
        "P8_Q2": LABEL_PAIRS[3],
        "P8_Q3": LABEL_PAIRS[3],

        "P11_Q1": LABEL_PAIRS[4],
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

    P5_Q1 = models.CurrencyField(
        min=0,
        label="How much money would you be willing to lend to that person?",
    )

    P6_Q1 = SliderField(label="You take a hitchhiker with you?")
    P6_Q2 = SliderField(label="You leave your personal belongings unattended in a public place?")
    P6_Q3 = SliderField(label="Do not lock your apartment door?")

    P7_Q1 = SliderField(label="In comparison to others I quickly build trust in strangers.")
    P7_Q2 = SliderField(label="Other people regard me as too credulous and trusting.")
    P7_Q3 = SliderField(label="I find it difficult to talk about personal issues with people I have not known for a long time yet.")
    P7_Q4 = SliderField(label="I assume that people have only the best intentions.")

    P8_Q1 = SliderField(label="In general, one can trust other people.")
    P8_Q2 = SliderField(label="Nowadays one cannot rely on anyone anymore.")
    P8_Q3 = SliderField(label="When dealing with strangers it is better to be careful before one relies on them.")

    P9_Q1 = models.StringField(
        label="Do you think...",
        choices=[
            "that most people would take advantage of you when they have the chance, or...",
            "that most people would be fair to you?",
        ],
        widget=widgets.RadioSelect,
    )

    P10_Q1 = models.StringField(
        label="Would you rather say...",
        choices=[
            "that most people try to be helpful, or...",
            "that most people only act in their own best interest?",
        ],
        widget=widgets.RadioSelect,
    )

    P11_Q1 = SliderField()


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


class Page_10(SurveyPage, SliderLabelsMixin):
    pass


class Page_11(SurveyPage, SliderLabelsMixin):
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
    Page_10,
    Page_11,
]
