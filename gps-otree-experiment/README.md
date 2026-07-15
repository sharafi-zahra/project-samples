# Global Preferences Survey — oTree Experiment

Python/[oTree](https://www.otree.org/) implementation of an incentivized economic-preferences
experiment used to collect data for a multi-country study of the Global Preferences Survey (GPS),
comparing experimentally-elicited preferences to their survey-based counterparts across countries
including Iran, China, Kenya, Colombia, and the USA.

## What it does

Each session runs participants through a sequence of incentivized tasks and matched survey
modules measuring six preference domains: risk taking, time (patience), trust, altruism, and
positive/negative reciprocity. Real monetary payoffs are computed from randomly selected
decisions, and participants are grouped/matched across rounds for the interactive games.

## Structure

Each folder under `src/` is a self-contained oTree app:

- `exp_risk`, `exp_time`, `exp_trust`, `exp_ultimatum`, `exp_prisoners_dilemma`, `exp_charitable` —
  incentivized experimental games (lottery choices, discounting tasks, trust game, ultimatum
  game, prisoner's dilemma, dictator/donation game)
- `survey_risk`, `survey_time`, `survey_trust`, `survey_altruism`, `survey_pn_reciprocity` —
  the matched qualitative/quantitative GPS survey items for each preference
- `demographic_characteristics`, `register`, `grouping`, `payment`, `third_dimension`,
  `unrelated`, `core` — session infrastructure (registration, participant grouping/matching,
  payment calculation, and shared page/model logic)
- `settings.py` — oTree session configuration (app sequence, currency, session parameters)

## Running it

```bash
pip install -r src/requirements.txt
cd src
otree devserver
```

Requires a `SECRET_KEY` and `OTREE_ADMIN_PASSWORD` environment variable to be set for anything
beyond local testing (see `settings.py`); no credentials are included in this repo.

## Note

This repo contains only the experiment source code. No participant data, response files, or
databases are included.
