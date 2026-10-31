"""Support-limited teacher rejection for structured Boolean Adult feature conditions."""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from btp.evaluation import sample_mixture
from btp.privacy import public_schema


class InvalidCondition(ValueError):
    pass


def _compile(node: dict, schema: dict, referenced: dict):
    if not isinstance(node, dict):
        raise InvalidCondition('Condition node must be an object')
    if 'and' in node or 'or' in node:
        key = 'and' if 'and' in node else 'or'
        if set(node) != {key} or not isinstance(node[key], list) or not node[key]:
            raise InvalidCondition(f'{key} requires a nonempty expression list')
        children = [_compile(child, schema, referenced) for child in node[key]]
        if key == 'and':
            return lambda frame: np.logical_and.reduce([c(frame) for c in children])
        return lambda frame: np.logical_or.reduce([c(frame) for c in children])
    if 'not' in node:
        if set(node) != {'not'}:
            raise InvalidCondition('not requires one expression')
        child = _compile(node['not'], schema, referenced)
        return lambda frame: ~child(frame)
    if set(node) == {'column', 'in'}:
        column = node['column']
        if column not in schema['categories'] or column == 'income':
            raise InvalidCondition('Categorical condition must name a public feature')
        values = node['in']
        if not isinstance(values, list) or not values or any(v not in schema['categories'][column] for v in values):
            raise InvalidCondition('Unknown/empty categorical set')
        referenced.setdefault(column, {'kind': 'category', 'values': set()})['values'].update(values)
        allowed = frozenset(values)
        return lambda frame: frame[column].astype(str).isin(allowed).to_numpy()
    if set(node) == {'column', 'between'}:
        column = node['column']
        if column not in schema['numeric_ranges']:
            raise InvalidCondition('Numeric condition must name a public numeric feature')
        limits = node['between']
        if not isinstance(limits, list) or len(limits) != 2 or any(not isinstance(v, int) for v in limits):
            raise InvalidCondition('Numeric interval needs two integer endpoints')
        lo, hi = limits
        public_lo, public_hi = map(int, schema['numeric_ranges'][column])
        if lo > hi or lo < public_lo or hi > public_hi:
            raise InvalidCondition('Contradictory or out-of-support interval')
        referenced.setdefault(column, {'kind': 'numeric', 'cuts': set()})['cuts'].update((lo, hi+1))
        return lambda frame: (pd.to_numeric(frame[column]).to_numpy() >= lo) & (pd.to_numeric(frame[column]).to_numpy() <= hi)
    raise InvalidCondition('Unsupported condition syntax')


@dataclass(frozen=True)
class AdultCondition:
    expression: dict
    evaluator: object

    def evaluate(self, frame: pd.DataFrame) -> np.ndarray:
        return np.asarray(self.evaluator(frame), bool)


def parse_condition(expression: dict, max_support_assignments: int = 100000) -> AdultCondition:
    schema = public_schema()
    referenced = {}
    evaluator = _compile(expression, schema, referenced)
    if not referenced:
        raise InvalidCondition('Condition has no feature atom')
    columns, domains = [], []
    for column, info in referenced.items():
        columns.append(column)
        if info['kind'] == 'category':
            domains.append(list(schema['categories'][column]))
        else:
            lo, hi = map(int, schema['numeric_ranges'][column])
            edges = sorted({lo, hi+1, *[cut for cut in info['cuts'] if lo <= cut <= hi+1]})
            domains.append([a for a, b in zip(edges[:-1], edges[1:]) if a < b])
    total = math.prod(len(domain) for domain in domains)
    if total > max_support_assignments:
        raise InvalidCondition('Condition support check exceeds declared complexity limit')
    possible = False
    for values in itertools.product(*domains):
        if evaluator(pd.DataFrame([dict(zip(columns, values))]))[0]:
            possible = True
            break
    if not possible:
        raise InvalidCondition('Condition is impossible within public support')
    return AdultCondition(expression, evaluator)


def generate(models: list, weights: np.ndarray, expression: dict, seed: int,
             accepted_rows: int = 1000, support_rows: int = 30000,
             min_support_count: int = 300, min_support_mass: float = .01,
             max_proposals: int = 200000) -> tuple[pd.DataFrame | None, dict]:
    condition = parse_condition(expression)
    if accepted_rows <= 0 or support_rows <= 0 or max_proposals <= 0:
        raise ValueError('Positive finite sampling budgets required')
    pilot, _ = sample_mixture(models, weights, support_rows, seed+13000)
    hits = int(condition.evaluate(pilot).sum())
    mass = hits/support_rows
    base = {'support_pilot_count': hits, 'support_pilot_mass': mass,
            'support_pilot_rows': support_rows, 'support_pilot_seed': seed+13000,
            'requested_accepted_rows': accepted_rows, 'maximum_proposals': max_proposals}
    if hits < min_support_count or mass < min_support_mass:
        return None, {**base, 'status': 'abstained_low_teacher_support',
                      'proposals': 0, 'accepted': 0}
    accepted, proposals = [], 0
    while sum(len(part) for part in accepted) < accepted_rows and proposals < max_proposals:
        batch_size = min(10000, max_proposals-proposals)
        batch, _ = sample_mixture(models, weights, batch_size, seed+14000+proposals//10000)
        proposals += batch_size
        accepted.append(batch.loc[condition.evaluate(batch)])
    count = sum(len(part) for part in accepted)
    if count < accepted_rows:
        return None, {**base, 'status': 'abstained_proposal_cap',
                      'proposals': proposals, 'accepted': count}
    result = pd.concat(accepted, ignore_index=True).iloc[:accepted_rows].copy()
    if not condition.evaluate(result).all():
        raise RuntimeError('Accepted conditional sample violates expression')
    return result, {**base, 'status': 'complete', 'proposals': proposals,
                    'accepted': len(result), 'violation_rate': 0.0}
