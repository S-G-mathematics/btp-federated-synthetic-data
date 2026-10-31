import numpy as np
import pandas as pd
import pytest
from btp.evaluation import Workload, Query, weighted_reference, sample_mixture, joint_posterior
from btp.run import conditional_reference
from btp.run import run_cell
from btp.models import fit_model


class Toy:
    def __init__(self,i): self.i=i
    def sample(self,n,seed):return pd.DataFrame({'client':[self.i]*n})


def test_exact_allocation_preserves_total_and_rounding():
    w=np.array([.13,.27,.6]);n=17
    frame,counts=sample_mixture([Toy(i) for i in range(3)],w,n,9)
    assert len(frame)==counts.sum()==n
    assert np.max(np.abs(counts-n*w))<1
    second,_=sample_mixture([Toy(i) for i in range(3)],w,n,9)
    pd.testing.assert_frame_equal(frame,second)


def test_reference_uses_target_mass_not_reference_row_count():
    q=Workload([Query('yes',(('income','eq','>50K'),))])
    parts=[pd.DataFrame({'income':['>50K']}),pd.DataFrame({'income':['<=50K']*99})]
    assert weighted_reference(parts,q,[.8,.2])[0]==.8


def test_conditional_reference_renormalizes_client_support():
    q=Workload([Query('high',(('income','eq','>50K'),))])
    parts=[pd.DataFrame({'age':[20,40],'income':['>50K','<=50K']}),
           pd.DataFrame({'age':[20]*10,'income':['<=50K']*10})]
    condition=Query('young',(('age','le',25),))
    vector,mass,count=conditional_reference(parts,[.8,.2],condition,q)
    assert np.isclose(mass,.6) and count==11
    assert np.isclose(vector[0],2/3)


def test_normalized_joint_posterior_matches_binary_mass():
    f=pd.DataFrame({'age':[20]*3+[30], 'income':['>50K']*3+['<=50K']})
    m=fit_model('independent',f,0,{'bins':2,'alpha':1})
    x=pd.DataFrame({'age':[20,30]})
    p=joint_posterior([m],[1],x)
    # Independence makes income posterior its smoothed marginal at every age.
    np.testing.assert_allclose(p,[4/6,4/6])


@pytest.mark.parametrize('selection',[None,{'method':'size','test_used_for_selection':True}])
def test_official_test_requires_valid_external_freeze(tmp_path,selection):
    raw=tmp_path/'data/raw';raw.mkdir(parents=True);(raw/'adult.zip').write_bytes(b'not opened before gate')
    path=None
    if selection is not None:
        import json
        path=tmp_path/'freeze.json';path.write_text(json.dumps(selection))
    with pytest.raises(ValueError,match='[Oo]fficial|[Ff]rozen'):
        run_cell(tmp_path,'smoke',{},'independent','age',5,101,[1],tmp_path/'out',10,True,path)
