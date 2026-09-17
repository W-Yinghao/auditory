import numpy as np
from auditory5.routes.route_a import fit_axis,project,fit_transforms,transform_summaries

def test_axes_training_center_and_scale_only():
    rng=np.random.default_rng(6);x=rng.normal(size=(20,12));axis=fit_axis(x)
    z=project(x,axis);np.testing.assert_allclose(z.mean(axis=0),0,atol=1e-12);np.testing.assert_allclose(z.std(axis=0),1)
    original=axis['center'].copy();project(x+100,axis);np.testing.assert_array_equal(original,axis['center'])

def test_background_adjustment_uses_no_test_fit():
    rng=np.random.default_rng(8)
    train={k:rng.normal(size=(1,24,2,p)) for k,p in [('post_delta',10),('pre_delta',6),('post_mean',10),('pre_mean',6),('quality',2)]}
    transforms=fit_transforms(train);test={k:v[:,:5] for k,v in train.items()}
    result=transform_summaries(test,transforms)
    assert result['post'].shape==(1,5,2,8) and result['pre'].shape==(1,5,2,6)
    assert set(result)=={'post','pre','background','background_adjusted','random_projection'}
