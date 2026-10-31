import pandas as pd
import pytest

from scripts.conditional_service import InvalidCondition, parse_condition


def test_structured_boolean_condition():
    condition = parse_condition({'and': [
        {'column': 'age', 'between': [25, 45]},
        {'or': [{'column': 'sex', 'in': ['Female']},
                {'column': 'education', 'in': ['Bachelors']}]}]})
    frame = pd.DataFrame({'age': [30, 30, 50], 'sex': ['Female', 'Male', 'Female'],
                          'education': ['HS-grad', 'HS-grad', 'Bachelors']})
    assert condition.evaluate(frame).tolist() == [True, False, False]


def test_impossible_and_malformed_abstain_before_sampling():
    with pytest.raises(InvalidCondition):
        parse_condition({'and': [
            {'column': 'age', 'between': [25, 30]},
            {'column': 'age', 'between': [40, 45]}]})
    with pytest.raises(InvalidCondition):
        parse_condition({'column': 'income', 'in': ['>50K']})
    with pytest.raises(InvalidCondition):
        parse_condition({'column': 'sex', 'in': ['Unlisted']})
