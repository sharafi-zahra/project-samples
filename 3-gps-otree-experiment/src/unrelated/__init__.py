from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'unrelated'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    QUESTIONS_SEQUESNCE = [
        ['good_at_math'],
    ]

    LABEL_PAIRS = [
        dict(
            least='Does not describe me at all',
            most='Describes me perfectly',
        ),
     ]

    SLIDER_LABELS = {
        'good_at_math': LABEL_PAIRS[0],
    }


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


def make_slider_field(label=None, **kwargs):
    label = label or ""
    field = models.IntegerField(
        label=label,
        choices=[0,1,2,3,4,5,6,7,8,9,10],
        widget=widgets.RadioSelectHorizontal(),
        **kwargs,
    )
    return field


class Player(BasePlayer):
    good_at_math = make_slider_field(
        label='I am good at math.',
    )

    q_cursor = models.IntegerField(initial=0)


# PAGES
class Question(Page):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player):
        return C.QUESTIONS_SEQUESNCE[player.q_cursor]

    def get_form(self, instance, formdata=None):
        form = super().get_form(instance, formdata)
        form.slider_form = False
        for question in form:
            if hasattr(question, "choices") and question.name in C.SLIDER_LABELS:
                form.slider_form = True
                question.least_label = C.SLIDER_LABELS[question.name]['least']
                question.most_label = C.SLIDER_LABELS[question.name]['most']

        return form

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.q_cursor += 1


page_sequence = [
    *[Question] * len(C.QUESTIONS_SEQUESNCE)
]
