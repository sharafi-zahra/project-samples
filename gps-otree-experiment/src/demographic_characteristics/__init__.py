from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'demographic_characteristics'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    QUESTIONS_SEQUESNCE = [
        'age',
        'gender',
        'program',
        'field',
        'studying_year',
        'academic_performance',
        'parents_education',
        'family_income_class',
        'prior_knowledge',
        'prior_knowledge_source',
    ]


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    age = models.IntegerField(
        label='How old are you?',
        help_text='years',
        min=1,
        max=1000,
    )
    gender = models.StringField(
        label='How would you describe your gender?',
        choices=[
            'Male',
            'Female',
            'Prefer not to say',
        ],
        widget=widgets.RadioSelect,
    )
    program = models.StringField(
        label='In what type of program are you now registered?',
        choices=[
            'Bachelor’s',
            'Master’s',
            'Doctorate',
            'Other',
        ],
        widget=widgets.RadioSelect,
    )
    field = models.StringField(
        label='What is your field of study?',
        choices=[
            'Law',
            'Medicine',
            'Economics',
            'Education',
            'Engineering',
            'Social sciences',
            'Natural sciences',
            'Management and business',
            'Journalism, media and communication',
            'Mathematics, statistics and informatic',
            'Humanities (Anthropology, art, history, language, literature, philosophy, religion)',
            'Others',
        ],
        widget=widgets.RadioSelect,
    )
    studying_year = models.IntegerField(
        label='In which year of your study are you now?',
        help_text='year',
        min=1,
        max=1000,
    )
    academic_performance = models.StringField(
        label='Which one best describes your academic performance in the university?',
        choices=[
            'Very low',
            'Low',
            'Medium',
            'High',
            'Very high',
            'Prefer not to say',
        ],
        widget=widgets.RadioSelect,
    )
    parents_education = models.StringField(
        label='What is the highest educational attainment achieved by either of your parents (or legal guardians)?',
        choices=[
            'Primary school',
            'Middle school',
            'High school',
            'Trade/vocational diploma or certificate',
            'College diploma or Certificate',
            'Bachelor',
            'Master',
            'Higher',
            'Prefer not to say',
        ],
        widget=widgets.RadioSelect,
    )
    family_income_class = models.StringField(
        label='Which one best describes your family income class?',
        choices=[
            'Upper (Wealthy) class',
            'Upper-middle class',
            'Middle-class',
            'Working-class',
            'Low-income',
            'Prefer not to say',
        ],
        widget=widgets.RadioSelect,
    )
    prior_knowledge = models.StringField(
        label='Did you have prior knowledge about the experiments of our study?',
        choices=[
            ['-', 'Not at all'],
            ['About some of them'] * 2,
            ['About all of them'] * 2,
        ],
        widget=widgets.RadioSelect,
    )
    prior_knowledge_source = models.StringField(
        label='From which source? (please select all which applies)',
    )
    prior_knowledge_source_choices = (
        'University courses',
        'Participation in other studies',
        'Friends who participated before me in this study',
    )

    q_cursor = models.IntegerField(initial=0)



# PAGES
class Question(Page):
    form_model = 'player'
    flag = True

    @staticmethod
    def get_form_fields(player):
        return [C.QUESTIONS_SEQUESNCE[player.q_cursor]]

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.q_cursor += 1

    @classmethod
    def is_displayed(cls, player):
        question = C.QUESTIONS_SEQUESNCE[player.q_cursor] if player.q_cursor < len(C.QUESTIONS_SEQUESNCE) else None
        if question == 'prior_knowledge_source' and player.prior_knowledge == '-':
            return False

        return True

    def get_form(self, instance, formdata=None):
        form = super().get_form(instance, formdata)
        for question in form:
            if question.name == 'prior_knowledge_source':
                question.choices_ = Player.prior_knowledge_source_choices

        return form


page_sequence = [
    *[Question] * len(C.QUESTIONS_SEQUESNCE)
]
