from otree.api import *

from core import (
    ExpPaymentAlert,
    ControlPage,
    ControlFailedPage,
    ControlPlayerMixin,
    ControlPassed,
    SimpleWaitPage,
    PayoffWaitPage,
    set_counters,
    set_groups,
)


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'exp_trust'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 4

    ENDOWMENT = cu(500)

    MULTIPLICATION_FACTORS = {
        1: 2,
        2: 2,
        3: 3,
        4: 3,
    }

    @classmethod
    def get_multiplication_factor(cls, round_number):
        return cls.MULTIPLICATION_FACTORS[round_number]

    CONTROL_CORRECT_ANSWERS = {
        'A': cu(500),
        'B': cu(650),
        'C': cu(500),
        'D': cu(500),
    }


class Subsession(BaseSubsession):
    exp_num = models.IntegerField()


def creating_session(subsession):
    set_groups(subsession)
    set_counters(subsession)


class Group(BaseGroup):

    def set_payoffs(self):
        sender = self.get_player_by_role('sender')
        recipient = self.get_player_by_role('recipient')

        endowment = C.ENDOWMENT
        transfer_amount = sender.transfer
        num = int(int(transfer_amount) / (int(endowment) / 10))
        transfer_back_amount = getattr(recipient, 'TB{}'.format(num))
        multiplication_factor = C.get_multiplication_factor(self.round_number)

        sender.payoff = endowment - transfer_amount + transfer_back_amount
        recipient.payoff = endowment + (transfer_amount * multiplication_factor) - transfer_back_amount


class Player(BasePlayer, ControlPlayerMixin):
    CP1_A = models.CurrencyField(min=0, max=1000000)
    CP1_B = models.CurrencyField(min=0, max=1000000)
    CP1_C = models.CurrencyField(min=0, max=1000000)
    CP1_D = models.CurrencyField(min=0, max=1000000)
    CP2_A = models.CurrencyField(min=0, max=1000000)
    CP2_B = models.CurrencyField(min=0, max=1000000)
    CP2_C = models.CurrencyField(min=0, max=1000000)
    CP2_D = models.CurrencyField(min=0, max=1000000)

    transfer =  models.CurrencyField(
        label="How many points do you want to transfer to the recipient?",
        choices=[
            0,
            50,
            100,
            150,
            200,
            250,
            300,
            350,
            400,
            450,
            500
        ]
    )

    # Transfer Back Fields
    TB0 = models.CurrencyField(label='', min=0)
    TB1 = models.CurrencyField(label='', min=0)
    TB2 = models.CurrencyField(label='', min=0)
    TB3 = models.CurrencyField(label='', min=0)
    TB4 = models.CurrencyField(label='', min=0)
    TB5 = models.CurrencyField(label='', min=0)
    TB6 = models.CurrencyField(label='', min=0)
    TB7 = models.CurrencyField(label='', min=0)
    TB8 = models.CurrencyField(label='', min=0)
    TB9 = models.CurrencyField(label='', min=0)
    TB10 = models.CurrencyField(label='', min=0)

    def role(self):
        if self.id_in_group == 1:
            if self.round_number % 2 == 0:
                return 'recipient'

            else:
                return 'sender'

        else:
            if self.round_number % 2 == 0:
                return 'sender'

            else:
                return 'recipient'

def TB0_max(player):
    multiplication_factor = C.get_multiplication_factor(player.round_number)
    return (0 * (C.ENDOWMENT / 10) * multiplication_factor) + C.ENDOWMENT

def TB1_max(player):
    multiplication_factor = C.get_multiplication_factor(player.round_number)
    return (1 * (C.ENDOWMENT / 10) * multiplication_factor) + C.ENDOWMENT

def TB2_max(player):
    multiplication_factor = C.get_multiplication_factor(player.round_number)
    return (2 * (C.ENDOWMENT / 10) * multiplication_factor) + C.ENDOWMENT

def TB3_max(player):
    multiplication_factor = C.get_multiplication_factor(player.round_number)
    return (3 * (C.ENDOWMENT / 10) * multiplication_factor) + C.ENDOWMENT

def TB4_max(player):
    multiplication_factor = C.get_multiplication_factor(player.round_number)
    return (4 * (C.ENDOWMENT / 10) * multiplication_factor) + C.ENDOWMENT

def TB5_max(player):
    multiplication_factor = C.get_multiplication_factor(player.round_number)
    return (5 * (C.ENDOWMENT / 10) * multiplication_factor) + C.ENDOWMENT

def TB6_max(player):
    multiplication_factor = C.get_multiplication_factor(player.round_number)
    return (6 * (C.ENDOWMENT / 10) * multiplication_factor) + C.ENDOWMENT

def TB7_max(player):
    multiplication_factor = C.get_multiplication_factor(player.round_number)
    return (7 * (C.ENDOWMENT / 10) * multiplication_factor) + C.ENDOWMENT

def TB8_max(player):
    multiplication_factor = C.get_multiplication_factor(player.round_number)
    return (8 * (C.ENDOWMENT / 10) * multiplication_factor) + C.ENDOWMENT

def TB9_max(player):
    multiplication_factor = C.get_multiplication_factor(player.round_number)
    return (9 * (C.ENDOWMENT / 10) * multiplication_factor) + C.ENDOWMENT

def TB10_max(player):
    multiplication_factor = C.get_multiplication_factor(player.round_number)
    return (10 * (C.ENDOWMENT / 10) * multiplication_factor) + C.ENDOWMENT


# PAGES
class Instructions_1(Page):

    def is_displayed(self):
        return self.round_number == 1


class Instructions_2(Page):
    pass


class Control(ControlPage):
    pass


class ControlFailed(ControlFailedPage):
    pass


class Transfer(Page):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player):
        if player.role() == 'sender':
            return ['transfer']

        elif player.role() == 'recipient':
            return ['TB{}'.format(i) for i in range(11)]

    def get_form(self, instance, formdata=None):
        multiplication_factor = C.get_multiplication_factor(self.round_number)
        form = super().get_form(instance, formdata)
        for i, field in enumerate(form):
            field.situation_data = {
                'sent': int(i * (C.ENDOWMENT / 10)),
                's': int(C.ENDOWMENT - (i * (C.ENDOWMENT / 10))),
                'r': int(C.ENDOWMENT + (i * (C.ENDOWMENT / 10) * multiplication_factor)),
            }

        return form



page_sequence = [
    ExpPaymentAlert,
    Instructions_1,
    Instructions_2,
    Control,
    Control,
    ControlFailed,
    ControlPassed,
    SimpleWaitPage,
    Transfer,
    PayoffWaitPage,
]
