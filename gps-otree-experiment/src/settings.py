from os import environ


PERFECT_STRANGER_WARNING = """
    <h5 class="alert alert-warning text-center" style="margin: 2rem;">
        WARNING: "Perfect Stranger" matching in this session requires at least 14 participants!
    </h5>
"""


SESSION_CONFIGS = [
    # *************** Predefined Sessions *************** #
    dict(
        name='session_a',
        display_name='Session A',
        num_demo_participants=2,
        doc=PERFECT_STRANGER_WARNING,
        app_sequence=[
            'register',
            'grouping',
            'exp_ultimatum',
            'exp_prisoners_dilemma',
            'survey_time',
            'exp_trust',
            'exp_charitable',
            'survey_risk',
            'unrelated',
            'payment',
        ],
    ),
    dict(
        name='session_b',
        display_name='Session B',
        num_demo_participants=1,
        app_sequence=[
            'register',
            'survey_pn_reciprocity',
            'exp_risk',
            'survey_altruism',
            'exp_time',
            'survey_trust',
            'payment',
        ],
    ),
    dict(
        name='session_c',
        display_name='Session C',
        num_demo_participants=1,
        app_sequence=[
            'register',
            'third_dimension',
            'demographic_characteristics',
        ],
    ),

    dict(
        name='session_a_c',
        display_name='Session A+C',
        participation_fee=10.00,
        num_demo_participants=2,
        doc=PERFECT_STRANGER_WARNING,
        app_sequence=[
            'register',
            'grouping',
            'exp_ultimatum',
            'exp_prisoners_dilemma',
            'survey_time',
            'exp_trust',
            'exp_charitable',
            'survey_risk',
            'unrelated',
            'third_dimension',
            'demographic_characteristics',
            'payment',
        ],
    ),
    dict(
        name='session_b_c',
        display_name='Session B+C',
        participation_fee=10.00,
        num_demo_participants=1,
        app_sequence=[
            'register',
            'survey_pn_reciprocity',
            'exp_risk',
            'survey_altruism',
            'exp_time',
            'survey_trust',
            'third_dimension',
            'demographic_characteristics',
            'payment',
        ],
    ),

    # ******************** Generals ******************** #
    dict(
        name='register',
        display_name='Register',
        num_demo_participants=1,
        app_sequence=['register'],
    ),

    # ******************** Surveys ******************** #
    dict(
        name='survey_trust',
        display_name='Trust (Survey)',
        num_demo_participants=1,
        app_sequence=['survey_trust'],
    ),
    dict(
        name='survey_altruism',
        display_name='Altruism (Survey)',
        num_demo_participants=1,
        app_sequence=['survey_altruism'],
    ),
    dict(
        name='survey_pn_reciprocity',
        display_name='Positive and Negative Reciprocity (Survey)',
        num_demo_participants=1,
        app_sequence=['survey_pn_reciprocity'],
    ),
    dict(
        name='survey_risk',
        display_name='Risk (Survey)',
        num_demo_participants=1,
        app_sequence=['survey_risk'],
    ),
    dict(
        name='survey_time',
        display_name='Time (Survey)',
        num_demo_participants=1,
        app_sequence=['survey_time'],
    ),

    # ******************** Others ******************** #
    dict(
        name='demographic_characteristics',
        display_name='Demographic Characteristics',
        num_demo_participants=1,
        app_sequence=['demographic_characteristics'],
    ),
    dict(
        name='third_dimension',
        display_name='Third Dimension',
        num_demo_participants=1,
        app_sequence=['third_dimension'],
    ),
    dict(
        name='unrelated',
        display_name='Unrelated',
        num_demo_participants=1,
        app_sequence=['unrelated'],
    ),

    # ******************** Experiments ******************** #
    dict(
        name='exp_trust',
        display_name='Trust (Experiment)',
        num_demo_participants=2,
        app_sequence=['exp_trust'],
    ),
    dict(
        name='exp_prisoners_dilemma',
        display_name='Prisoners Dilemma (Experiment)',
        num_demo_participants=2,
        app_sequence=['exp_prisoners_dilemma'],
    ),
    dict(
        name='exp_ultimatum',
        display_name='Ultimatum (Experiment)',
        num_demo_participants=2,
        app_sequence=['exp_ultimatum'],
    ),
    dict(
        name='exp_charitable',
        display_name='Charitable (Experiment)',
        num_demo_participants=1,
        app_sequence=['exp_charitable'],
    ),
    dict(
        name='exp_risk',
        display_name='Risk (Experiment)',
        num_demo_participants=1,
        app_sequence=['exp_risk'],
    ),
    dict(
        name='exp_time',
        display_name='Time (Experiment)',
        num_demo_participants=1,
        app_sequence=['exp_time'],
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.008,
    participation_fee=00.00,
    doc="",
)

PARTICIPANT_FIELDS = [
    'exp_time_payoff',
]
SESSION_FIELDS = [
    'grouping_matrixes',
    'experiment_counter',
    'survey_counter',
]

DEBUG = True

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """Welcome!"""

SECRET_KEY = environ.get('OTREE_SECRET_KEY', 'CHANGE_ME_BEFORE_DEPLOYING')

SURVEY_CURRENCY = 'Euro'

##########################################

DEBUG = False

# ADMIN_USERNAME = 'admin'
# ADMIN_PASSWORD = 'admin'

LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'EUR'
SURVEY_CURRENCY = 'Euro'
