from collections import namedtuple
from copy import copy

from otree.api import *

from settings import SURVEY_CURRENCY


doc = """
Your app description
"""


LotteryPrize = namedtuple('LotteryPrize', 'win lose')


class Subsession(BaseSubsession):
    pass


def set_groups(subsession):
    grouping_matrixes = subsession.session.vars.get('grouping_matrixes')
    if grouping_matrixes:
        from grouping import C as GC

        exp_name = subsession.get_folder_name()
        exp_rounds = list(GC.EXP_ROUNDS_RANGE[exp_name])
        matrix_index = exp_rounds[subsession.round_number - 1]
        matrix = grouping_matrixes[matrix_index]
        subsession.set_group_matrix(matrix)

    else:
        subsession.group_randomly(fixed_id_in_group=True)


def set_counters(subsession):
    if not subsession.session.vars.get('experiment_counter'):
        subsession.session.experiment_counter = 0

    if not subsession.session.vars.get('survey_counter'):
        subsession.session.survey_counter = 0

    app_name = subsession.get_folder_name()
    if app_name.startswith('exp_'):
        if subsession.round_number == 1:
            subsession.session.experiment_counter += 1

        subsession.exp_num = copy(subsession.session.experiment_counter)

    elif app_name.startswith('survey_'):
        if subsession.round_number == 1:
            subsession.session.survey_counter += 1

        subsession.survey_num = copy(subsession.session.survey_counter)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    condition = models.StringField()
    selected_situation = models.IntegerField()


class ControlPlayerMixin:

    @property
    def control_correct_answers(self):
        return self.subsession._Constants.CONTROL_CORRECT_ANSWERS

    @property
    def first_control_round(self):
        first_round_fields_values = [self.field_maybe_none(field) for field in dir(self) if field.startswith('CP1_')]
        return all(value is None for value in first_round_fields_values)

    @property
    def first_control_failed(self):
        first_round_answers = {
            field.split('_')[-1]: self.field_maybe_none(field)
            for field in dir(self)
            if field.startswith('CP1_')
        }
        return first_round_answers != self.control_correct_answers

    @property
    def second_control_failed(self):
        first_round_answers = {
            field.split('_')[-1]: self.field_maybe_none(field)
            for field in dir(self)
            if field.startswith('CP2_')
        }
        return first_round_answers != self.control_correct_answers



def SliderField(label=None, **kwargs):
    label = label or ""
    field = models.IntegerField(
        label=label,
        choices=[0,1,2,3,4,5,6,7,8,9,10],
        widget=widgets.RadioSelectHorizontal(),
        **kwargs,
    )
    return field



# PAGES
class FirstRoundOnlyPage(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class ExpPaymentAlert(FirstRoundOnlyPage):
    pass


class ControlPage(Page):
    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        if player.round_number != 1:
            return False

        if player.first_control_round:
            return True

        elif player.first_control_failed:
            return True

        else:
            return False

    @staticmethod
    def get_form_fields(player):
        if player.first_control_round:
            return [field for field in dir(player) if field.startswith('CP1_')]

        else:
            return [field for field in dir(player) if field.startswith('CP2_')]

    @staticmethod
    def vars_for_template(player):
        wrong_answer = True
        if player.first_control_round:
            wrong_answer = False

        elif not player.first_control_failed:
            wrong_answer = False

        return {'wrong_answer': wrong_answer}

    @staticmethod
    def before_next_page(player, timeout_happened):
        pass


class ControlFailedPage(Page):

    @staticmethod
    def is_displayed(player):
        if player.round_number != 1:
            return False

        if player.first_control_failed and player.second_control_failed:
            return True


class ControlPassed(Page):

    @staticmethod
    def is_displayed(player):
        if player.round_number != 1:
            return False

        if not player.first_control_failed:
            return True

        elif not player.second_control_failed:
            return True

        else:
            return False


class SurveyPaymentAlert(FirstRoundOnlyPage):
    pass


class SliderFormPage(Page):
    def get_form(self, instance, formdata=None):
        form = super().get_form(instance, formdata)
        form.slider_form = False
        for question in form:
            if hasattr(question, "choices") and question.name in self.slider_labels:
                form.slider_form = True
                question.least_label = self.slider_labels[question.name]['least']
                question.most_label = self.slider_labels[question.name]['most']

        return form


class SurveyPage(SliderFormPage):
    form_model = 'player'

    @classmethod
    def page_number(cls):
        return cls.__name__.split("_")[1]

    @classmethod
    def get_form_fields(cls, player):
        return [att for att in dir(player) if att.startswith(f"P{cls.page_number()}_")]

    @staticmethod
    def js_vars(player):
        return dict(
            survey_currency=SURVEY_CURRENCY,
        )


class RiskDecision(Page):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player):
        situation = player.s_cursor
        return [f'R{situation}']

    @staticmethod
    def vars_for_template(player):
        return {
            'situation': player.s_cursor + 1,
            'lottery_prize': player.subsession._Constants.LOTTERY_PRIZE,
            'sure_price': player.current_sure_price,
        }

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.s_cursor += 1


def set_payoffs(subsession):
    for group in subsession.get_groups():
            group.set_payoffs()


class PayoffWaitPage(WaitPage):
    body_text = "Waiting for the other participants."
    wait_for_all_groups = True
    after_all_players_arrive = set_payoffs


class SimpleWaitPage(WaitPage):
    body_text = "Waiting for the other participants."


class EndingSurveyWaitPage(WaitPage):
    body_text = "Waiting for the other participants."
    wait_for_all_groups = True
