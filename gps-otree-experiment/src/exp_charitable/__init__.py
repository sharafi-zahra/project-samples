from otree.api import *

from core import (
    ExpPaymentAlert,
    ControlPage,
    ControlFailedPage,
    ControlPlayerMixin,
    ControlPassed,
    PayoffWaitPage,
    set_counters
)


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'charitable'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    ENDOWMENT = cu(300)

    CONTROL_CORRECT_ANSWERS = {
        'A': cu(0),
        'B': cu(300),
    }


class Subsession(BaseSubsession):
    exp_num = models.IntegerField()


def creating_session(subsession):
    set_counters(subsession)


class Group(BaseGroup):

    def set_payoffs(self):
        players = self.get_players()

        for player in players:
            player.set_payoff()


class Player(BasePlayer, ControlPlayerMixin):
    CP1_A = models.CurrencyField(
        label='',
        min=0,
    )
    CP1_B = models.CurrencyField(
        label='',
        min=0,
    )
    CP2_A = models.CurrencyField(
        label='',
        min=0,
    )
    CP2_B = models.CurrencyField(
        label='',
        min=0,
    )

    donation = models.CurrencyField(
        min=0,
        max=C.ENDOWMENT,
        label='You will now receive an amount of 300 points. How many of these points would you like to donate?',
    )
    organization = models.StringField(
        label="Which organization should receive your donation?",
        choices=[
            ['Brot für die Welt'] * 2,
            ['Kindernothilfe'] * 2,
            ['Red Cross'] * 2,
            ['Welthungerhilfe'] * 2,
            ['BUND (German Federation for the Environment and Nature Conservation)'] * 2,
            ['Greenpeace'] * 2,
            ['Terre des Hommes'] * 2,
            ['Aktion Mensch'] * 2,
            ['-', 'Others (This has to be an officially registered Charitable organization)'],
        ],
        widget=widgets.RadioSelect(),
    )
    other_organization = models.StringField(
        label='If you chose "Others", insert the name of organization in this field',
        blank=True,
    )

    def set_payoff(self):
        self.payoff = C.ENDOWMENT - self.donation


# PAGES
class Instructions(Page):
    pass


class Control(ControlPage):
    pass


class ControlFailed(ControlFailedPage):
    pass


class Donate(Page):
    form_model = 'player'
    form_fields = ['donation']


class Organization(Page):
    form_model = 'player'
    form_fields = ['organization', 'other_organization']

    @staticmethod
    def is_displayed(player):
        return player.donation > 0

    @staticmethod
    def error_message(player, values):
        if values["organization"] == '-':
            if not values["other_organization"]:
                return 'When you choose "Others", you have to fill the name of organization!'

        else:
            if values["other_organization"]:
                return 'Only when you choose "Others", you can fill the name of organization!'


page_sequence = [
    ExpPaymentAlert,
    Instructions,
    Control,
    Control,
    ControlFailed,
    ControlPassed,
    Donate,
    Organization,
    PayoffWaitPage,
]
