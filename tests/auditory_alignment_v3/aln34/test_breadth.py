"""Protect inherited training/evaluation algorithms and added cohort isolation."""
import ast
from pathlib import Path

from auditory_alignment_v3.aln34 import breadth_inner as I


def definition(module, name):
    tree=ast.parse((Path('auditory_alignment_v3/aln34')/(module+'.py')).read_text())
    node=next(x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==name)
    class Normalize(ast.NodeTransformer):
        def visit_Constant(self,n):
            if isinstance(n.value,str):
                n.value=n.value.replace('ALN34_BREADTH_BUDGET','ALN34_BUDGET2').replace('ALN34_BREADTH_SPLIT','ALN34_SPLIT')
            return n
        def visit_Assert(self,n):
            if isinstance(n.msg,ast.Constant) and n.msg.value=='cohort metadata drift':return None
            return self.generic_visit(n)
    return ast.dump(Normalize().visit(node),include_attributes=False)


def test_inherited_training_and_evaluation_bodies_unchanged():
    pairs=(('learning_budget_v2','breadth_budget',('instrumentation','run_one')),
           ('data_inner','breadth_inner',('instrumentation','evaluation_view','run_one')),
           ('adaptation_policy','breadth_policy',('Adapter','Bundle','rebuild','run_unit')),
           ('strong_fusion','breadth_fusion',('evaluate_pair','run_unit')),
           ('episode_training','breadth_episode',('continue_source','evaluate_model','run_unit')))
    for old,new,names in pairs:
        for name in names:
            assert definition(old,name)==definition(new,name),(old,new,name)


def meta():
    people=[{'id':f'p{i}','group':'HC','fold':i,'dev':False,'test_only':False} for i in range(5)]
    people += [{'id':'development','group':'HC','fold':-1,'dev':True,'test_only':False},
               {'id':'phantom','group':'Artifact','fold':-1,'dev':False,'test_only':True}]
    segments=[]
    for p in range(len(people)):
        for role in ('fit','es','test'):
            for part in ('a','b'):
                segments.append({'p':p,'role':role,'kind':'ss','uid':role+part,'part':part,'e0':0,'s0':0})
    return {'participants':people,'segments':segments}


def test_phantom_never_trains_and_independent_dev_never_in_panel():
    m=meta();s=I.selection(m,0,0,'inner_person',1.)
    assert s['train_ids']==['development','p2','p3','p4']
    assert s['inner_ids']==['p1'] and s['outer_ids']==['p0']
    assert all(m['segments'][i]['p'] not in (0,1,6) for i in s['fit_indices']+s['es_indices'])


def test_people_subsets_nested_without_phantom():
    m=meta();a=I.selection(m,0,0,'people',.25);b=I.selection(m,0,0,'people',.5)
    assert set(a['train_ids'])<=set(b['train_ids'])
    assert 'phantom' not in b['train_ids'] and 'p0' not in b['train_ids']
