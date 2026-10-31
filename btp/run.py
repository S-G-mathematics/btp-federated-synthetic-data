"""Sequential, checkpointed experiment driver. Run via python -m btp.run.

The evaluator may read real records. The release-only fitting functions receive
models, synthetic pilots and explicitly permitted summaries; score-based
calibration is labeled privileged. This is a research simulation, not networking.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, os, pickle, platform, sys, time, traceback
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import yaml
from scipy.special import logsumexp
from .data import prepare_splits, build_partition_rule, PREDICTORS
from .models import fit_model
from .weights import solve_weights
from .privacy import public_schema, fit_private_histogram, fit_nonprivate_public_histogram
from .projection import EducationNumberProjection
from .projected_workload import projected_workloads_v2
from .evaluation import (public_workloads, weighted_reference, empirical_metrics,
    column_metrics, KernelFeatures, sample_mixture, predictor, predictive_metrics,
    joint_posterior, probability_metrics, CONDITIONS, Workload)
from .operators import fit_operator, refit_operator_weights


def write_json(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    def convert(x):
        if isinstance(x,np.ndarray): return x.tolist()
        if isinstance(x,np.generic): return x.item()
        if isinstance(x,Path): return str(x)
        raise TypeError(type(x).__name__)
    def clean(x):
        if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
        if isinstance(x,(list,tuple)):return [clean(v) for v in x]
        if isinstance(x,np.ndarray):return clean(x.tolist())
        if isinstance(x,np.generic):return clean(x.item())
        if isinstance(x,float) and not np.isfinite(x):return None
        return x
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(clean(value),indent=2,default=convert,allow_nan=False)+'\n')
    tmp.replace(path)


def save_pickle(path, obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_bytes(pickle.dumps(obj));tmp.replace(path)


def code_hash():
    h=hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob('*.py')):
        h.update(path.name.encode());h.update(path.read_bytes())
    return h.hexdigest()


def param_grid(name, profile):
    if profile.get('smoke'):
        if name=='prototype_kde': return [{'centers':8,'bandwidth_multiplier':1.0,'alpha':.2,
                                           'minimum_center_support':5,'n_init':1}]
        if name=='latent_class': return [{'bins':8,'components':2,'alpha':.2,
                                         'max_iter':80,'n_init':1}]
        return [{'bins':8,'alpha':.2,'components':2,'max_iter':60,'n_init':1}]
    if name=='mixed_gmm': return [{'components':c,'alpha':a,'max_iter':300,'n_init':2}
        for c,a in [(2,.1),(2,1.),(4,.1),(4,1.),(8,.1),(8,1.),
                    (12,.1),(12,1.),(16,.1)]]
    if name=='prototype_kde': return [{'centers':c,'bandwidth_multiplier':h,'alpha':.5,
                                        'minimum_center_support':10,'n_init':2}
        for c in [16,32,64] for h in [.75,1.25]]
    if name=='latent_class': return [{'bins':16,'components':c,'alpha':a,
                                      'max_iter':200,'n_init':2}
        for c in [2,4,8] for a in [.1,1.]]
    if name=='independent': return [{'bins':b,'alpha':a}
        for b in [8,16,32,64] for a in [.1,1.]]
    return [{'bins':b,'alpha':a} for b in [8,16,32] for a in [.1,1.]]


def tune_client(name, train, tune, workload, schema, seed, profile):
    trials=[];best=None
    for j,parameters in enumerate(param_grid(name,profile)):
        settings={**parameters,'numeric_bounds':schema['numeric_ranges'],
                  'category_vocab':schema['categories']}
        start=time.monotonic()
        try:
            raw_model=fit_model(name,train,seed+j,settings)
            model=(EducationNumberProjection(raw_model,
                schema['education_number_map'],tuple(schema['numeric_ranges']['education-num']))
                if profile.get('structural_projection') else raw_model)
            sample=model.sample(int(profile['tune_samples']),seed+100+j)
            error=float(np.mean(np.abs(workload.mean(tune)-workload.mean(sample))))
            finite_fraction=float(np.isfinite(model.log_prob(tune.iloc[:min(64,len(tune))])).mean())
            diagnostics={}
            if hasattr(raw_model,'gmm'):
                diagnostics={'converged':bool(raw_model.gmm.converged_),
                             'iterations':int(raw_model.gmm.n_iter_),
                             'lower_bound':float(raw_model.gmm.lower_bound_)}
            elif hasattr(raw_model,'converged'):
                diagnostics={'converged':bool(raw_model.converged),
                             'iterations':int(raw_model.iterations),
                             'lower_bound':float(raw_model.lower_bound)}
            elif hasattr(raw_model,'component_counts'):
                diagnostics={'centers':int(len(raw_model.component_counts)),
                             'minimum_center_count':int(raw_model.component_counts.min()),
                             'bandwidth':raw_model.bandwidth.tolist(),
                             'kmeans_iterations':int(raw_model.kmeans_iterations)}
            eligible=bool(np.isfinite(error) and finite_fraction==1. and
                          diagnostics.get('converged',True))
            trials.append({'parameters':parameters,'local_tune_query_mae':error,
                           'wall_seconds':time.monotonic()-start,
                           'train_rows':int(len(train)),'tune_rows':int(len(tune)),
                           'finite_tune_score_fraction':finite_fraction,
                           'invalid_income_rate':float((~sample['income'].isin(['<=50K','>50K'])).mean()),
                           'likelihood_kind':model.likelihood_kind,
                           'diagnostics':diagnostics,
                           'status':'eligible' if eligible else 'nonconverged_or_invalid'})
            if eligible and (best is None or error<best[0]): best=(error,model,parameters)
        except Exception as exc:
            trials.append({'parameters':parameters,'status':'failed',
                           'error':f'{type(exc).__name__}: {exc}',
                           'wall_seconds':time.monotonic()-start})
    if best is None:
        raise RuntimeError(f'no eligible local {name} model for client after {len(trials)} recorded trials: {trials}')
    return best[1],best[2],trials


def row_likelihood(models,frame):
    ll=np.column_stack([m.log_prob(frame) for m in models])
    # A floor is only a numerical/support safeguard, never hidden.
    nonfinite=int(np.sum(~np.isfinite(ll)))
    return np.nan_to_num(ll,nan=-1e6,neginf=-1e6,posinf=1e6),nonfinite


def draw(candidate,models,n,seed):
    if candidate['operator'] is not None: return candidate['operator'].sample(n,seed)
    return sample_mixture(models,candidate['weights'],n,seed)[0]


def select_release_method(validation_rows):
    # Development validation uses only the registered primary workload.
    # The unseen interaction workload is an untouched audit endpoint.
    allowed=[r for r in validation_rows if r['access']=='released_models_and_permitted_summaries']
    if not allowed: raise ValueError('no release-only validation candidate')
    if any(not np.isfinite(r['query_linf']) for r in allowed):
        raise ValueError('nonfinite primary validation loss')
    return min(allowed,key=lambda r:(r['query_linf'],r['method']))['method']


def conditional_reference(parts,alpha,condition,workload):
    masses=np.array([condition.evaluate(f).mean() for f in parts])
    mass=float(np.dot(alpha,masses))
    if mass==0: return None,0.,0
    numerator=np.zeros(len(workload.queries)); count=0
    for f,a in zip(parts,alpha):
        mask=condition.evaluate(f).astype(bool); count+=int(mask.sum())
        numerator+=a*(workload.transform(f)*mask[:,None]).mean(axis=0)
    return numerator/mass,mass,count


def run_cell(root,profile_name,profile,generator,kind,k,seed,experiments,out,wall_seconds,
             official_test=False,selection_file=None):
    if official_test:
        raise ValueError('Legacy multi-method official-test route is disabled; use the dedicated full-freeze confirmation runner')
    started=time.monotonic(); root=Path(root)
    raw_hash=hashlib.sha256((root/'data/raw/adult.zip').read_bytes()).hexdigest()
    frozen=None
    if official_test:
        if selection_file is None or not Path(selection_file).is_file():
            raise ValueError('Official test requires an existing --selection-file frozen from development validation')
        frozen=json.loads(Path(selection_file).read_text())
        if not frozen.get('method') or frozen.get('test_used_for_selection',True):
            raise ValueError('Frozen selection needs method and test_used_for_selection:false')
    specification={'profile_name':profile_name,'profile':profile,'generator':generator,
        'partition':kind,'k':k,'seed':seed,'code_hash':code_hash(),'raw_sha256':raw_hash}
    if profile.get('structural_projection'):
        specification['workload_version']='projected_v2'
        specification['projection']='public_education_number_pushforward_v1'
    else:
        specification['workload_version']='historical_v1'
    specification['reference_role']='official_test_confirmation' if official_test else 'development_assessment'
    specification['frozen_selection']=frozen
    digest=hashlib.sha256(json.dumps(specification,sort_keys=True).encode()).hexdigest()[:16]
    cell=Path(out)/f'{generator}_{kind}_k{k}_s{seed}_{digest}'
    cell.mkdir(parents=True,exist_ok=True)
    write_json(cell/'configuration.json',specification)
    write_json(cell/'environment.json',{'python':sys.version,'platform':platform.platform(),
               'pid':os.getpid(),'started_utc':datetime.now(timezone.utc).isoformat()})
    def log(message):
        line=f'{datetime.now(timezone.utc).isoformat()} {message}'
        print(line,flush=True)
        with (cell/'execution.log').open('a') as f:f.write(line+'\n')
    def phase(number,fn):
        marker=cell/f'exp{number:02d}_complete.json'
        if number not in experiments:return
        if marker.exists():log(f'Exp {number}: cached');return
        if time.monotonic()-started>wall_seconds:raise TimeoutError('cell wall budget exhausted')
        log(f'Exp {number}: starting'); t=time.monotonic(); fn()
        write_json(marker,{'status':'completed','wall_seconds':time.monotonic()-t,
                          'scope':'mechanical_smoke' if profile.get('smoke') else 'measured_research_run'})
        log(f'Exp {number}: completed')
    schema=public_schema()
    splits=prepare_splits(root/'data/raw',seed=seed)
    if not official_test:
        # Preserve full-record duplicate groups while creating an independent
        # development assessment from the original validation pool. Official
        # test rows are not scored or used for winner selection in this mode.
        validation=splits['validation']
        mask=[]
        for row in validation.itertuples(index=False,name=None):
            digest_row=hashlib.sha256(repr(tuple(row)).encode()).digest()
            mask.append(int.from_bytes(digest_row[:8],'big')%2==0)
        mask=np.asarray(mask)
        splits['validation']=validation.loc[mask].copy()
        splits['test']=validation.loc[~mask].copy()
    if profile.get('train_cap'):
        for name in ['train','tune','calibration','validation','test']:
            cap=int(profile['train_cap'] if name=='train' else profile['reference_cap'])
            f=splits[name];splits[name]=f.sample(min(cap,len(f)),random_state=seed).sort_index()
    rule=build_partition_rule(splits['train'],k,kind,seed,float(profile['severity']))
    parts={name:[f.loc[rule.assign(f)==i] for i in range(k)]
           for name,f in splits.items() if name!='quarantine'}
    counts=np.array([len(f) for f in parts['train']]);alpha=counts/counts.sum()
    for name,groups in parts.items():
        if min(map(len,groups))<2:raise ValueError(f'empty/tiny {name} client; invalid partition, no silent repair')
    manifest=[]
    for name,f in splits.items():
        if name=='quarantine':continue
        labels=rule.assign(f)
        manifest.extend({'row_id':str(idx),'split':name,'client':int(c)} for idx,c in zip(f.index,labels))
    pd.DataFrame(manifest).to_csv(cell/'partition_manifest.csv',index=False)
    write_json(cell/'partition.json',{'alpha':alpha,'counts':counts,'rule':rule.__dict__,
        'split_client_sizes':{s:list(map(len,p)) for s,p in parts.items()},
        'test_reference_role':specification['reference_role'],
        'target':'training client mass; empirical references weighted by this same alpha'})
    workload,audit=(projected_workloads_v2(schema) if profile.get('structural_projection')
                    else public_workloads(schema))
    write_json(cell/'workloads.json',{'calibration':workload.to_dict(),'unseen_audit':audit.to_dict()})
    models=[];parameters=[]
    for i in range(k):
        checkpoint=cell/'releases'/f'client_{i}.pkl'
        tuning=cell/'client_private'/f'tuning_{i}.json'
        if checkpoint.exists() and tuning.exists():
            models.append(pickle.loads(checkpoint.read_bytes()));parameters.append(json.loads(tuning.read_text())['selected'])
        else:
            log(f'training {generator} client {i}, n={counts[i]}')
            m,p,trials=tune_client(generator,parts['train'][i],parts['tune'][i],workload,schema,seed+31*i,profile)
            models.append(m);parameters.append(p);save_pickle(checkpoint,m)
            write_json(tuning,{'selected':p,'trials':trials,'used_split':'local tune only'})
    n_pilot=int(profile['pilot_samples'])
    pilots=[m.sample(n_pilot,seed+900+i) for i,m in enumerate(models)]
    values=[workload.transform(f) for f in pilots]
    H=np.column_stack([x.mean(0) for x in values])
    bcal=weighted_reference(parts['calibration'],workload,alpha)
    bval=weighted_reference(parts['validation'],workload,alpha)
    target_cov=sum(a*a*np.cov(workload.transform(f),rowvar=False)/len(f) for f,a in zip(parts['calibration'],alpha))
    pilot_cov=sum(a*a*np.cov(x,rowvar=False)/len(x) for x,a in zip(values,alpha))
    residual_cov=target_cov+pilot_cov+1e-5*np.eye(len(bcal))
    kernel=KernelFeatures(workload,int(profile.get('kernel_features',48)))
    kernelH=np.column_stack([kernel.transform(f).mean(0) for f in pilots])
    kernelb=sum(a*kernel.transform(f).mean(0) for a,f in zip(alpha,parts['calibration']))
    # Only these aggregate quantities go to the release-only statistical server.
    np.savez_compressed(cell/'releases'/'permitted_summary.npz',alpha=alpha,H=H,
        target_query_mean=bcal,residual_cov=residual_cov,kernelH=kernelH,kernelb=kernelb)
    write_json(cell/'releases'/'release_contract.json',{'formal_dp':False,
        'messages':['fitted local models','public schema and counts','calibration query means and covariance','kernel feature means'],
        'public_education_number_map':schema['education_number_map'] if profile.get('structural_projection') else None,
        'projected_sampler_and_score':bool(profile.get('structural_projection')),
        'projected_score_kind':models[0].likelihood_kind if profile.get('structural_projection') else None,
        'workload_version':specification['workload_version'],
        'warning':'these unnoised extra summaries are not private; DP baseline is separate',
        'raw_row_access':'client-side training and privileged evaluator only'})
    ll,support_floor_count=row_likelihood(models,pd.concat(parts['calibration']))
    methods=['uniform','size','moment_l2','query_minimax','entropy_calibration','uncertainty_gls',
             'pseudo_bma_logscore','predictive_evidence_bma','stacking_logscore',
             'kernel_mean_matching','robust_query_calibration']
    candidates={};weight_records=[]
    for method in methods:
        privileged=method in ['stacking_logscore','pseudo_bma_logscore','predictive_evidence_bma']
        settings={'sizes':counts,'penalty':float(profile.get('entropy_penalty',100.)),
            'covariance':residual_cov,'radius':1.,
            'model_var':np.column_stack([x.var(0)/len(x) for x in values]),
            'target_var':np.diag(target_cov),'privileged':True,
            'sample_weights':sum(map(len,parts['calibration']))*np.concatenate([np.full(len(p),a/len(p)) for p,a in zip(parts['calibration'],alpha)])}
        mh,mb=(kernelH,kernelb) if method=='kernel_mean_matching' else (H,bcal)
        r=solve_weights(method,mh,mb,alpha,seed,settings,ll if privileged else None)
        access='privileged_real_calibration_scores' if privileged else 'released_models_and_permitted_summaries'
        weight_records.append({'method':method,'access':access,'success':r['success'],
            'weights':r['weights'],'objective':r['objective'],'details':r['details']})
        if r['success']:candidates[method]={'weights':r['weights'],'operator':None,'access':access}
    for name in ['logpool','barycenter']:
        op=fit_operator('entropic_barycenter' if name=='barycenter' else name,models,alpha,workload.transform,bcal,seed,
            {'support_size':int(profile['support_size']),'pilot_per_model':min(n_pilot,500),
             'numeric_bounds':schema['numeric_ranges'],'iterations':1000,
             'maxiter':200,'weight_candidate_draws':int(profile.get('barycenter_weight_trials',4))})
        valid=op.details.get('optimizer_success',op.details.get('converged',True))
        if not valid:
            weight_records.append({'method':name,'success':False,'details':op.details})
            continue
        candidates[name]={'weights':op.weights,'operator':op,'access':'released_models_and_permitted_summaries'}
        save_pickle(cell/'releases'/f'{name}.pkl',op)
        weight_records.append({'method':name,'access':candidates[name]['access'],'success':True,
                              'weights':op.weights,'details':op.details})
    write_json(cell/'weight_fits.json',{'methods':weight_records,'likelihood_floor_count':support_floor_count,
       'likelihood_kind':models[0].likelihood_kind,'eight_families':'see docs/WEIGHT_METHODS.md; auxiliary baselines do not add novel families'})
    m=int(profile['synthetic_rows']); val_rows=[]
    for name,c in candidates.items():
        syn=draw(c,models,m,seed+4200)
        metrics=empirical_metrics(parts['validation'],syn,workload,audit,alpha)
        val_rows.append({'method':name,'access':c['access'],**metrics})
    # Winner is selected before any assessment/test metrics are computed or read.
    winner=(frozen['method'] if frozen is not None else select_release_method(val_rows))
    if winner not in candidates:raise RuntimeError('Frozen method failed or is unavailable; do not replace it using test results')
    write_json(cell/'selection_frozen.json',{'method':winner,'selection_split':'external frozen policy' if frozen else 'validation',
        'selection_metric':'primary validation query_linf; deterministic method-name tie break',
        'audit_used_for_selection':False,'test_used':False,
        'scope':'within this cell; campaign-wide confirmatory selection must use development cases only'})
    selected=candidates[winner]
    selected_ds=draw(selected,models,m,seed+5200)
    selected_ds.to_csv(cell/'synthetic_selected.csv.gz',index=False,compression={'method':'gzip','mtime':0})

    def exp1():
        pd.DataFrame(val_rows).to_csv(cell/'exp01_validation.csv',index=False)
        rows=[]
        for name,c in candidates.items():
            for rep in range(int(profile['repeats'])):
                syn=draw(c,models,m,seed+5200+rep)
                rows.append({'method':name,'access':c['access'],'replicate':rep,
                    **empirical_metrics(parts['test'],syn,workload,audit,alpha)})
        pd.DataFrame(rows).to_csv(cell/'exp01_test.csv',index=False)
        pd.DataFrame(column_metrics(parts['test'],selected_ds,alpha,schema['numeric_ranges'])).to_csv(cell/'exp01_columns.csv',index=False)
    phase(1,exp1)

    def exp2():
        r=solve_weights('oracle_query_minimax',H,bval,alpha)
        if not r['success']:raise RuntimeError('oracle LP failed')
        osyn=sample_mixture(models,r['weights'],m,seed+5200)[0]
        om=empirical_metrics(parts['test'],osyn,workload,audit,alpha)
        rows=[];operator_benchmarks={}
        for name,c in candidates.items():
            sm=empirical_metrics(parts['test'],draw(c,models,m,seed+5200),workload,audit,alpha)
            baseline=om;comparator_weights=r['weights'];certificate='exact LP for fixed empirical H'
            if c['operator'] is not None:
                operator_oracle=refit_operator_weights(c['operator'],bval,seed,
                    {'restarts':3 if profile.get('smoke') else 8,'weight_candidate_draws':int(profile.get('barycenter_weight_trials',4))})
                valid=operator_oracle.details.get('optimizer_success',operator_oracle.details.get('converged',True))
                operator_benchmarks[name]={'valid':valid,'details':operator_oracle.details}
                if not valid:
                    rows.append({'method':name,'status':'best_found_operator_benchmark_failed'});continue
                baseline=empirical_metrics(parts['test'],operator_oracle.sample(m,seed+5200),workload,audit,alpha)
                comparator_weights=operator_oracle.weights;certificate='best found, no global optimum claim'
            rows.append({'method':name,'same_family':True,
                'comparator_family':'finite_support_operator' if c['operator'] is not None else 'mixture',
                'certificate':certificate,
                'test_query_gap':sm['query_linf']-baseline['query_linf'],
                'weight_l1_diagnostic':float(np.abs(c['weights']-comparator_weights).sum())})
        pd.DataFrame(rows).to_csv(cell/'exp02_oracle_gaps.csv',index=False)
        write_json(cell/'exp02_oracle.json',{'solver':r,'oracle_test':om,
            'certificate':'exact LP only for fixed empirical H and validation query vector',
            'operator_same_support_best_found':operator_benchmarks,
            'nonlinear_operators':'own same-support best-found validation benchmarks; no global-optimum claims'})
    phase(2,exp2)

    def exp3():
        w=selected['weights']; b=max(1,k//2); eff=np.zeros(k); subsets=[]
        for start in range(k):
            indices=np.array([(start+j)%k for j in range(b)])
            mass=w[indices].sum()
            if mass==0:continue
            within=w[indices]/mass; rho=mass/b;eff[indices]+=rho*within
            subsets.append({'clients':indices,'rho':rho,'within_weights':within})
        write_json(cell/'exp03_subsets.json',{'subsets':subsets,'effective_weights':eff,
            'max_identity_error':float(np.max(np.abs(eff-w))),
            'applies_to':'pure mixture construction only; does not claim nonlinear operator equivalence'})
        assert np.allclose(eff,w)
    phase(3,exp3)

    def exp4():
        rows=[]
        for size in profile['sample_sizes']:
            for rep in range(int(profile['repeats'])):
                ds=draw(selected,models,int(size),seed+6100+rep)
                row={'m':size,'replicate':rep,**empirical_metrics(parts['test'],ds,workload,audit,alpha),
                    'hoeffding_fixedL_95':float(np.sqrt(np.log(2*len(workload.queries)/.05)/(2*size)))}
                if ds.income.nunique()==2:
                    pm=predictive_metrics(predictor(ds,'logistic',seed),parts['test'],alpha)
                    row.update({'TSTR_'+key:value for key,value in pm.items()})
                rows.append(row)
        pd.DataFrame(rows).to_csv(cell/'exp04_sample_size.csv',index=False)
    phase(4,exp4)

    feature_workload=Workload([q for q in workload.queries if all(t[0]!='income' for t in q.terms)])
    conditional_rows=[]
    def exp5():
        teacher=draw(selected,models,int(profile['conditional_pool']),seed+7000)
        for index,condition in enumerate(CONDITIONS):
            subset=teacher.loc[condition.evaluate(teacher).astype(bool),list(PREDICTORS)]
            teacher_mass=len(subset)/len(teacher)
            minimum_rows=int(profile.get('conditional_min_support',20))
            minimum_mass=float(profile.get('conditional_min_mass',.01))
            # The deployable abstention decision uses only generated teacher
            # support and declared thresholds, never real held-out support.
            server_supported=bool(len(subset)>=minimum_rows and teacher_mass>=minimum_mass)
            record={'condition':condition.name,'teacher_support':len(subset),
                    'teacher_pool':len(teacher),'teacher_mass':teacher_mass,
                    'minimum_teacher_rows':minimum_rows,'minimum_teacher_mass':minimum_mass,
                    'server_supported':server_supported}
            reference,mass,count=conditional_reference(parts['test'],alpha,condition,feature_workload)
            record.update({'real_mass':mass,'real_reference_count':count})
            if not server_supported:
                record['status']='abstain_insufficient_teacher_support';conditional_rows.append(record);continue
            model=fit_model('chow_liu',subset,seed+index,{'bins':8,'alpha':.1})
            raw=model.sample(int(profile['conditional_rows']),seed+7100+index)
            record['raw_violation']=float(1-condition.evaluate(raw).mean())
            accepted=raw.loc[condition.evaluate(raw).astype(bool)]
            record['accepted_rows']=len(accepted)
            if not len(accepted):record['status']='abstain_no_valid_generated_rows'
            else:
                if reference is None:
                    record.update({'status':'assessment_reference_unavailable',
                                   'conditional_query_linf':None,'conditional_query_mae':None,
                                   'postfilter_violation':0.})
                else:
                    error=np.abs(feature_workload.mean(accepted)-reference)
                    record.update({'status':'completed','conditional_query_linf':float(error.max()),
                        'conditional_query_mae':float(error.mean()),'postfilter_violation':0.})
                accepted.to_csv(cell/f'exp05_{index}_conditional.csv.gz',index=False)
                save_pickle(cell/'releases'/f'conditional_{index}.pkl',model)
            conditional_rows.append(record)
        pd.DataFrame(conditional_rows).to_csv(cell/'exp05_conditionals.csv',index=False)
    phase(5,exp5)

    def exp6():
        rows=[]
        names=['logistic'] if profile.get('smoke') else ['logistic','extra_trees']
        for name in names:
            for source,frame in [('synthetic',selected_ds),('real_reference',splits['train'])]:
                model=predictor(frame,name,seed)
                rows.append({'predictor':name,'trained_on':source,'privileged':source=='real_reference',
                             'client':'target_weighted_global',
                             **predictive_metrics(model,parts['test'],alpha)})
                for i,client_reference in enumerate(parts['test']):
                    rows.append({'predictor':name,'trained_on':source,'privileged':source=='real_reference',
                        'client':str(i),**predictive_metrics(model,[client_reference],[1.])})
                save_pickle(cell/('releases' if source=='synthetic' else 'evaluator_private')/f'{name}_{source}.pkl',model)
        pd.DataFrame(rows).to_csv(cell/'exp06_prediction.csv',index=False)
    phase(6,exp6)

    def exp7():
        real=pd.concat(parts['test']);weights=np.concatenate([np.full(len(p),a/len(p)) for p,a in zip(parts['test'],alpha)])
        y=(real.income=='>50K').astype(int).to_numpy()
        if selected['operator'] is None:
            prob=joint_posterior(models,selected['weights'],real[list(PREDICTORS)])
            good=np.isfinite(prob)
            result=probability_metrics(y[good],prob[good],weights[good]) if good.any() else {}
            result.update({'supported_fraction':float(good.mean()),'route':'mixture joint likelihood',
                'likelihood_kind':models[0].likelihood_kind,
                'exact_probability_claim':models[0].likelihood_kind=='exact_discretized'})
        else:
            result={'status':'finite-support joint abstains off support',
                'kernel_smoothed_posterior_is_separate_estimator':True,
                'required_followup':'evaluate exact supported-X coverage separately; do not call kernel smoother the exact joint posterior'}
        write_json(cell/'exp07_joint_predictor.json',result)
    phase(7,exp7)

    def exp8():
        allq=workload.queries+audit.queries;wq=Workload(allq)
        r=weighted_reference(parts['test'],wq,alpha);s=wq.mean(selected_ds)
        pd.DataFrame({'query':[q.name for q in allq],'real_D_R':r,'synthetic_D_S':s,
                      'abs_error':np.abs(r-s),'used_in_calibration':[True]*len(workload.queries)+[False]*len(audit.queries)}).to_csv(cell/'exp08_queries.csv',index=False)
    phase(8,exp8)

    def exp9():
        rows=[]
        for name in ['uniform','size',winner]:
            ds=draw(candidates[name],models,m,seed+8100)
            rows.append({'ablation':name,**empirical_metrics(parts['test'],ds,workload,audit,alpha)})
        pd.DataFrame(rows).to_csv(cell/'exp09_ablations.csv',index=False)
        if selected['operator'] is None:
            student=predictor(selected_ds,'logistic',seed)
            features=draw(selected,models,min(m,1000),seed+8200)[list(PREDICTORS)]
            teacher=joint_posterior(models,selected['weights'],features)
            pred=student.predict_proba(features)[:,1];good=np.isfinite(teacher)
            write_json(cell/'exp09_consistency.json',{'teacher_student_mse':float(np.mean((teacher[good]-pred[good])**2)),
                       'supported_fraction':float(good.mean()),'interpretation':'internal consistency, not real-data fidelity'})
    phase(9,exp9)

    def exp10():
        # Exact empirical telescoping identity; no unknown TV estimated from samples.
        r=weighted_reference(parts['test'],workload,alpha)
        final_pilot=workload.mean(draw(selected,models,n_pilot,seed+9000))
        s=workload.mean(selected_ds);w=selected['weights']
        terms=[r-H@alpha,H@alpha-H@w,H@w-final_pilot,final_pilot-s]
        residual=float(np.max(np.abs(sum(terms)-(r-s))))
        write_json(cell/'exp10_empirical_decomposition.json',{
            'terms':['local fidelity plus reference/pilot uncertainty','weight correction','operator change plus pilot uncertainty','finite synthetic draws'],
            'linf_terms':[float(np.max(np.abs(x))) for x in terms],
            'observed_D_R_D_S_linf':float(np.max(np.abs(r-s))),
            'telescoping_residual':residual,'not_a_population_TV_estimate':True})
        rows=[]
        fractions=[.5,1.] if profile.get('smoke') else [.25,.5,1.]
        for fraction in fractions:
            smaller=[]
            for i,f in enumerate(parts['train']):
                sub=f.sample(max(2,int(len(f)*fraction)),random_state=seed)
                settings={**parameters[i],'numeric_bounds':schema['numeric_ranges'],'category_vocab':schema['categories']}
                smaller.append(fit_model(generator,sub,seed+i,settings))
            syn=sample_mixture(smaller,alpha,m,seed+9100)[0]
            rows.append({'training_fraction':fraction,**empirical_metrics(parts['test'],syn,workload,audit,alpha)})
        pd.DataFrame(rows).to_csv(cell/'exp10_training_size.csv',index=False)
    phase(10,exp10)

    def exp11():
        rows=[]
        for condition in CONDITIONS:
            rc,rm,count=conditional_reference(parts['test'],alpha,condition,feature_workload)
            smask=condition.evaluate(selected_ds).astype(bool);sm=float(smask.mean())
            if rc is None or sm==0:
                rows.append({'condition':condition.name,'status':'unsupported','real_mass':rm,'synthetic_mass':sm});continue
            scond=feature_workload.mean(selected_ds.loc[smask])
            real_joint=rc*rm
            synthetic_joint=(feature_workload.transform(selected_ds)*smask[:,None]).mean(0)
            joint_error=float(np.max(np.abs(real_joint-synthetic_joint)))
            mass_error=abs(rm-sm);bound=min(1.,(joint_error+mass_error)/rm)
            actual=float(np.max(np.abs(rc-scond)))
            assert actual<=bound+1e-9
            rows.append({'condition':condition.name,'status':'completed','real_mass':rm,'synthetic_mass':sm,
                'observed_conditional_error':actual,'empirical_ratio_bound':bound,
                'interpretation':'deterministic finite-query empirical ratio bound, not estimated population TV'})
        pd.DataFrame(rows).to_csv(cell/'exp11_error_transfer.csv',index=False)
    phase(11,exp11)

    def exp12():
        from sklearn.metrics import roc_auc_score
        rows=[];ledgers=[];attack_rows=[]
        nonprivate=[fit_nonprivate_public_histogram(f,schema=public_schema(n_public=len(f),bins=8)) for f in parts['train']]
        reference=sample_mixture(nonprivate,alpha,m,seed+10100)[0]
        rows.append({'epsilon_single_release':None,'mechanism':'matched NONPRIVATE public-bin histograms',
            **empirical_metrics(parts['test'],reference,workload,audit,alpha),
            'serialized_model_bytes':sum(len(pickle.dumps(p)) for p in nonprivate)})
        for epsilon in profile['privacy_epsilons']:
            private=[]
            for i,frame in enumerate(parts['train']):
                ps=public_schema(n_public=len(frame),bins=8)
                model=fit_private_histogram(frame,float(epsilon),None,schema=ps)
                private.append(model);ledgers.append({'epsilon_setting':epsilon,'client':i,**model.privacy_ledger})
                n=min(300,len(frame),len(parts['test'][i]))
                members=frame.sample(n,random_state=seed)
                nonmembers=parts['test'][i].sample(n,random_state=seed)
                score=np.r_[model.log_prob(members),model.log_prob(nonmembers)]
                attack_rows.append({'epsilon':epsilon,'client':i,'members':n,'nonmembers':n,
                    'likelihood_membership_auc':float(roc_auc_score(np.r_[np.ones(n),np.zeros(n)],score)),
                    'threat_model':'attacker knows released density and candidate record; higher likelihood means member',
                    'limitation':'diagnostic on real train vs held-out nonmembers, possibly affected by distribution shift; not a DP proof',
                    'reference_role':specification['reference_role']})
            syn=sample_mixture(private,alpha,m,seed+10100)[0]
            rows.append({'epsilon_single_release':epsilon,'mechanism':'public-bin independent private histograms',
                **empirical_metrics(parts['test'],syn,workload,audit,alpha),
                'serialized_model_bytes':sum(len(pickle.dumps(p)) for p in private)})
            save_pickle(cell/'private_baseline_releases'/f'epsilon_{epsilon}.pkl',private)
        pd.DataFrame(rows).to_csv(cell/'exp12_privacy_utility.csv',index=False)
        pd.DataFrame(attack_rows).to_csv(cell/'exp12_membership_diagnostic.csv',index=False)
        write_json(cell/'exp12_privacy_ledger.json',{'individual_releases':ledgers,
            'epsilon_for_releasing_all_settings_same_cell':float(sum(profile['privacy_epsilons'])),
            'conditions':['fixed public client membership and sizes','replace-one adjacency','fixed public schema and clipping'],
            'full_bundle_is_NOT_DP':'contains raw public Adult and nonprivate model outputs; guarantee covers specified histogram mechanisms only',
            'cross_seed_composition':'sum applicable per-run budgets if releasing all runs on overlapping individuals'})
        write_json(cell/'exp12_resources.json',{'elapsed_cell_wall_seconds':time.monotonic()-started,
            'released_model_bytes':sum(p.stat().st_size for p in (cell/'releases').glob('*.pkl')),
            'summary_bytes':(cell/'releases/permitted_summary.npz').stat().st_size,
            'raw_rows_shared_with_statistical_server':0,
            'privileged_score_baselines':'calibration likelihood matrix computed in evaluator; excluded from deployable claim'})
    phase(12,exp12)
    write_json(cell/'STATUS.json',{'status':'completed_requested_phases','experiments':experiments,
        'winner_validation':winner,'elapsed_seconds':time.monotonic()-started,
        'scope':'smoke-only; no scientific ranking' if profile.get('smoke') else 'one measured configuration; aggregate independent seeds before conclusions'})
    log(f'completed requested phases; winner-on-validation={winner}')
    return str(cell)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',default='configs/campaign.yaml')
    ap.add_argument('--profile',default='smoke');ap.add_argument('--generator',default='independent')
    ap.add_argument('--partition',default='age');ap.add_argument('--clients',type=int,default=5)
    ap.add_argument('--seed',type=int,default=101);ap.add_argument('--experiments',default='1,2')
    ap.add_argument('--out',default='results');ap.add_argument('--wall-seconds',type=int,default=3600)
    ap.add_argument('--official-test',action='store_true');ap.add_argument('--selection-file')
    args=ap.parse_args();root=Path(__file__).resolve().parents[1]
    config=yaml.safe_load((root/args.config).read_text());p=config['profiles'][args.profile]
    exps=list(range(1,13)) if args.experiments=='all' else [int(x) for x in args.experiments.split(',')]
    if any(x<1 or x>12 for x in exps):ap.error('experiments must be 1..12')
    try:
        run_cell(root,args.profile,p,args.generator,args.partition,args.clients,args.seed,exps,
            root/args.out if not Path(args.out).is_absolute() else args.out,args.wall_seconds,
            args.official_test,args.selection_file)
    except Exception:
        traceback.print_exc();raise


if __name__=='__main__':main()
