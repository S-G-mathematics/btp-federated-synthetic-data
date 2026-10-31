"""Empirical D_R versus D_S metrics, fixed public workloads and predictors.

This module belongs to the privileged research evaluator. It is not a server
API and its real-row arguments must never enter a deployable release artifact.
All primary fidelity results compare datasets, not unknown population laws.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import roc_auc_score, balanced_accuracy_score, f1_score, brier_score_loss
from .data import NUMERIC, PREDICTORS


@dataclass(frozen=True)
class Query:
    name: str
    terms: tuple  # (column, operator, value) conjunction

    def evaluate(self, frame):
        mask = np.ones(len(frame), dtype=bool)
        for column, op, value in self.terms:
            if op == "eq": mask &= frame[column].astype(str).to_numpy() == str(value)
            elif op == "le": mask &= pd.to_numeric(frame[column]).to_numpy() <= value
            elif op == "gt": mask &= pd.to_numeric(frame[column]).to_numpy() > value
            elif op == "between":
                a = pd.to_numeric(frame[column]).to_numpy()
                mask &= (a >= value[0]) & (a <= value[1])
            else: raise ValueError(op)
        return mask.astype(float)


class Workload:
    def __init__(self, queries): self.queries = list(queries)
    def transform(self, frame):
        return np.column_stack([q.evaluate(frame) for q in self.queries])
    def mean(self, frame):
        if not len(frame): return np.full(len(self.queries), np.nan)
        return self.transform(frame).mean(axis=0)
    def to_dict(self): return [asdict(q) for q in self.queries]


def public_workloads(schema):
    """Predeclared public bins/categories. No query selected from test data."""
    queries = []
    thresholds = {"age": [25,35,45,55,65], "fnlwgt": [100000,200000,300000],
                  "education-num": [8,9,10,12,13,16], "capital-gain": [0,1000,5000,10000],
                  "capital-loss": [0,1000,2000], "hours-per-week": [20,35,40,50,60]}
    for c, values in thresholds.items():
        for v in values: queries.append(Query(f"{c}<={v}", ((c,"le",v),)))
    for c, values in schema["categories"].items():
        for v in values: queries.append(Query(f"{c}={v}", ((c,"eq",v),)))
    for c, values in {"sex":["Female","Male"], "education":["HS-grad","Bachelors","Masters"],
                      "workclass":["Private","Self-emp-not-inc","Local-gov"]}.items():
        for v in values:
            queries.append(Query(f"{c}={v}&income>50K", ((c,"eq",v),("income","eq",">50K"))))
    audit = []
    for lo,hi in [(17,30),(31,45),(46,60),(61,90)]:
        for sex in ["Female","Male"]:
            for income in ["<=50K",">50K"]:
                terms=(("age","between",(lo,hi)),("sex","eq",sex),("income","eq",income))
                audit.append(Query(f"age{lo}-{hi}&{sex}&{income}",terms))
    for ed in ["HS-grad","Bachelors","Masters"]:
        for work in ["Private","Self-emp-not-inc"]:
            audit.append(Query(f"audit:{ed}&{work}&income",(("education","eq",ed),("workclass","eq",work),("income","eq",">50K"))))
    return Workload(queries), Workload(audit)


def weighted_reference(parts, workload, alpha):
    means = []
    for p,a in zip(parts,alpha):
        if a > 0 and len(p)==0: raise ValueError("target client has no reference rows")
        means.append(workload.mean(p) if len(p) else np.zeros(len(workload.queries)))
    return np.asarray(alpha) @ np.asarray(means)


def empirical_metrics(real_parts, synth, workload, audit, alpha):
    """Target-alpha-weighted empirical D_R versus D_S query distances."""
    real_q=weighted_reference(real_parts,workload,alpha); syn_q=workload.mean(synth)
    real_a=weighted_reference(real_parts,audit,alpha); syn_a=audit.mean(synth)
    err=np.abs(real_q-syn_q); extra=np.abs(real_a-syn_a)
    return {"query_linf":float(err.max()),"query_mae":float(err.mean()),
            "unseen_query_linf":float(extra.max()),"unseen_query_mae":float(extra.mean()),
            "invalid_income_rate":float((~synth.income.isin(["<=50K",">50K"])).mean()),
            "unique_row_fraction":float(len(synth.drop_duplicates())/len(synth)),
            "n_synthetic":len(synth),"n_real_reference":sum(map(len,real_parts)),
            "reference":"weighted empirical client D_R; alpha fixed from training"}


def column_metrics(real_parts, synth, alpha, bounds):
    real=pd.concat(real_parts)
    weights=np.concatenate([np.full(len(p),a/len(p)) for p,a in zip(real_parts,alpha)])
    rows=[]
    for c in real.columns:
        if c in NUMERIC:
            lo,hi=bounds[c]
            value=wasserstein_distance(real[c],synth[c],u_weights=weights)/max(hi-lo,1)
            metric="public_range_normalized_wasserstein"
        else:
            p=pd.Series(weights).groupby(real[c].astype(str).to_numpy()).sum()
            q=synth[c].astype(str).value_counts(normalize=True)
            idx=p.index.union(q.index)
            value=.5*np.abs(p.reindex(idx,fill_value=0)-q.reindex(idx,fill_value=0)).sum()
            metric="categorical_TV"
        rows.append({"column":c,"metric":metric,"value":float(value)})
    return rows


class KernelFeatures:
    """Fixed random Fourier embedding of public query vectors, in [0,1]."""
    def __init__(self, workload, dimension=64, seed=2718, bandwidth=1.0):
        self.workload=workload
        rng=np.random.default_rng(seed)
        self.omega=rng.normal(size=(len(workload.queries),dimension))/bandwidth
        self.phase=rng.uniform(0,2*np.pi,dimension)
    def transform(self, frame):
        x=self.workload.transform(frame)/np.sqrt(len(self.workload.queries))
        return (1+np.cos(x@self.omega+self.phase))/2


def sample_mixture(models, weights, n, seed):
    """Largest remainder allocation: exact total, <=1-row rounding per client."""
    w=np.asarray(weights,float)
    if np.any(w<0) or not np.isclose(w.sum(),1): raise ValueError("invalid mixture weights")
    exact=n*w; counts=np.floor(exact).astype(int)
    counts[np.argsort(-(exact-counts),kind="stable")[:n-counts.sum()]]+=1
    samples=[model.sample(int(c),seed+1009*(i+1)) for i,(model,c) in enumerate(zip(models,counts)) if c]
    frame=pd.concat(samples,ignore_index=True)
    return frame.sample(frac=1,random_state=seed).reset_index(drop=True),counts


def predictor(frame, name="logistic", seed=0):
    columns=[c for c in PREDICTORS if c in frame]
    nums=[c for c in columns if c in NUMERIC]; cats=[c for c in columns if c not in nums]
    transform=ColumnTransformer([("numeric",StandardScaler(),nums),
        ("categorical",OneHotEncoder(handle_unknown="ignore",sparse_output=False),cats)])
    clf=(LogisticRegression(max_iter=600,random_state=seed) if name=="logistic"
         else ExtraTreesClassifier(n_estimators=120,min_samples_leaf=3,n_jobs=1,random_state=seed))
    model=make_pipeline(transform,clf)
    y=(frame.income==">50K").astype(int)
    if y.nunique()<2: raise ValueError("predictor requires both income classes")
    return model.fit(frame[columns],y)


def predictive_metrics(model, real_parts, alpha):
    real=pd.concat(real_parts); y=(real.income==">50K").astype(int).to_numpy()
    p=np.clip(model.predict_proba(real[list(PREDICTORS)])[:,1],0,1)
    weights=np.concatenate([np.full(len(f),a/len(f)) for f,a in zip(real_parts,alpha)])
    return probability_metrics(y,p,weights)


def probability_metrics(y,p,weights=None):
    y=np.asarray(y);p=np.asarray(p)
    w=np.ones(len(y))/len(y) if weights is None else np.asarray(weights)/np.sum(weights)
    ece=0.
    for a,b in zip(np.linspace(0,1,11)[:-1],np.linspace(0,1,11)[1:]):
        take=(p>=a)&(p<b if b<1 else p<=b)
        if take.any(): ece+=w[take].sum()*abs(np.average(y[take],weights=w[take])-np.average(p[take],weights=w[take]))
    return {"auroc":float(roc_auc_score(y,p,sample_weight=w)) if len(np.unique(y))==2 else None,
            "balanced_accuracy":float(balanced_accuracy_score(y,p>=.5,sample_weight=w)) if len(np.unique(y))==2 else None,
            "f1":float(f1_score(y,p>=.5,sample_weight=w,zero_division=0)),
            "brier":float(brier_score_loss(y,p,sample_weight=w)),"ece_fixed10":float(ece)}


def joint_posterior(models,weights,features):
    from scipy.special import logsumexp
    records=[]
    for label in ["<=50K",">50K"]:
        f=features.copy();f["income"]=label
        scores=np.column_stack([m.log_prob(f) for m in models])
        records.append(logsumexp(scores+np.log(np.maximum(weights,1e-300)),axis=1))
    denominator=np.logaddexp(records[0],records[1])
    result=np.exp(records[1]-denominator)
    result[~np.isfinite(result)]=np.nan
    return result


CONDITIONS=[
    Query("age25-45",(("age","between",(25,45)),)),
    Query("female",(("sex","eq","Female"),)),
    Query("bachelors_age30-60",(("education","eq","Bachelors"),("age","between",(30,60)))),
    Query("rare_doctorate_age60-90",(("education","eq","Doctorate"),("age","between",(60,90)))),
]
