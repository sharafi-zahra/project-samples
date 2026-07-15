from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'third_dimension'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    QUESTIONS_SEQUESNCE = [
        ['height'],
        ['weight'],
        ['smoker'],
        ['exerciser'],
        ['save_money'],
        ['invest_money'],
        ['social_participation', 'social_participation_organization'],
        ['social_participation_hours'],
        ['reuse_bags'],
        ['conserve_water'],
        ['reuse_cups'],
        ['close_friends'],
        ['education_plan'],
        ['exam_prepration'],
        ['sport_preferation'],
        ['friendship_duration'],
    ]


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    height = models.IntegerField(
        label='How tall are you? (if you don’t know, please estimate)',
        help_text='cm',
        min=1,
        max=1000,
    )
    weight = models.IntegerField(
        label='How many kilograms do you currently weigh? (if you don’t know, please estimate)',
        help_text='kg',
        min=1,
        max=1000,
    )
    smoker = models.BooleanField(
        label='Do you currently smoke, be it cigarettes, a pipe, or cigars?',
        choices=[
            [True, 'Yes'],
            [False, 'No'],
        ],
        widget=widgets.RadioSelect,
    )
    exerciser = models.BooleanField(
        label='Do you exercise or do sports regularly?',
        choices=[
            [True, 'Yes'],
            [False, 'No'],
        ],
        widget=widgets.RadioSelect,
    )
    save_money = models.BooleanField(
        label='Do you save money?',
        choices=[
            [True, 'Yes'],
            [False, 'No'],
        ],
        widget=widgets.RadioSelect,
    )
    invest_money = models.BooleanField(
        label='Do you invest in securities (e.g., stocks, funds, bonds, equity warrants)?',
        choices=[
            [True, 'Yes'],
            [False, 'No'],
        ],
        widget=widgets.RadioSelect,
    )
    social_participation = models.BooleanField(
        label='''
            Do you participate in any social organization (e.g., charity, community
            or neighborhood committee, religious group, cultural or sports group,
            education-oriented programs or groups, environment conservation,
            labor union, political party)?
        ''',
        choices=[
            [True, 'Yes'],
            [False, 'No'],
        ],
        widget=widgets.RadioSelect,
    )
    social_participation_organization = models.StringField(
        label='If Yes, what organization(s)?',
        blank=True,
    )
    social_participation_hours = models.IntegerField(
        label='What are the average hours in a month you spend in social organizations?',
        help_text='hours',
        min=0,
        max=1000,
    )
    reuse_bags = models.BooleanField(
        label='Do you regularly use reusable bags when shopping?',
        choices=[
            [True, 'Yes'],
            [False, 'No'],
        ],
        widget=widgets.RadioSelect,
    )
    conserve_water = models.BooleanField(
        label='Do you regularly conserve water when it is not directly needed?',
        choices=[
            [True, 'Yes'],
            [False, 'No'],
        ],
        widget=widgets.RadioSelect,
    )
    reuse_cups = models.BooleanField(
        label='Do you regularly use a reusable cup/container for drinking?',
        choices=[
            [True, 'Yes'],
            [False, 'No'],
        ],
        widget=widgets.RadioSelect,
    )
    close_friends = models.IntegerField(
        label='How many close friends do you have?',
        min=0,
        max=1000,
    )

    education_plan = models.StringField(
        label='Do you plan to pursue a higher level of education or go to the job market directly after your study?',
        choices=[
            'Pursue a higher level of education',
            'Go to the job market directly',
        ],
        widget=widgets.RadioSelect,
    )
    exam_prepration = models.StringField(
        label='Do you spend more time preparing for exams in advance or rather only prepare shortly before the exam?',
        choices=[
            'Preparing for exams in advance',
            'Prepare shortly before the exam',
        ],
        widget=widgets.RadioSelect,
    )
    sport_preferation = models.StringField(
        label='Do you prefer team-oriented sports or individual-oriented sports?',
        choices=[
            'Team-oriented sports',
            'Individual-oriented sports',
        ],
        widget=widgets.RadioSelect,
    )

    friendship_duration = models.IntegerField(
        label='On average, what is the relationship duration between you and your close friends?',
        help_text='months',
        min=0,
        max=1000,
    )

    q_cursor = models.IntegerField(initial=0)




# PAGES
class Question(Page):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player):
        return C.QUESTIONS_SEQUESNCE[player.q_cursor]

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.q_cursor += 1


page_sequence = [
    *[Question] * len(C.QUESTIONS_SEQUESNCE)
]
