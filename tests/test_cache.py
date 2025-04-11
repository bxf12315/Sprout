from sprout.common.model_cache.cache import cached_loading
import pytest


@pytest.fixture
def cache():
    cached_loading("../isolation_forest_model.joblib")
    cached_loading("../isolation_forest_model.joblib")
