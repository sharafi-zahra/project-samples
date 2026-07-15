from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'payment'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass


# PAGES
class Payment(Page):

    @staticmethod
    def vars_for_template(player):
        session = player.session
        participant = player.participant

        general_payments = {
            'participation_fee': session.config['participation_fee'],
            'payoff': {
                'point': participant.payoff,
                'real_currency': participant.payoff.to_real_world_currency(session),
            },
            'sum': participant.payoff_plus_participation_fee(),
        }
        exp_time_payments = None
        total_payoff = {
            'today': general_payments['sum'],
            'future': cu(0).to_real_world_currency(session),
        }

        # breakpoint()
        if 'exp_time_payoff' in participant.vars:
            exp_time_payments = {
                0: [],
                12: [],
                'sum': {
                    0: {'point': cu(0), 'real_currency': cu(0).to_real_world_currency(session)},
                    12: {'point': cu(0), 'real_currency': cu(0).to_real_world_currency(session)},
                    'all': {'point': cu(0), 'real_currency': cu(0).to_real_world_currency(session)},
                },
            }
            for payment in participant.exp_time_payoff:
                point = payment['amount']
                real_currency = point.to_real_world_currency(session)
                date = payment['date']
                detailed_payment = {
                    'point': point,
                    'real_currency': real_currency,
                }
                exp_time_payments[date].append(detailed_payment)
                exp_time_payments['sum'][date]['point'] += point
                exp_time_payments['sum'][date]['real_currency'] += real_currency
                exp_time_payments['sum']['all']['point'] += point
                exp_time_payments['sum']['all']['real_currency'] += real_currency

            for payments in exp_time_payments.values():
                if isinstance(payments, list):
                    while len(payments) < 2:
                        payments.append(None)

            total_payoff['today'] += exp_time_payments['sum'][0]['real_currency']
            total_payoff['future'] += exp_time_payments['sum'][12]['real_currency']

        return {
            'general_payments': general_payments,
            'exp_time_payments': exp_time_payments,
            'total_payoff': total_payoff,
        }



page_sequence = [
    Payment,
]
