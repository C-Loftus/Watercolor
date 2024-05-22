import pytest
from lib import Singleton


def test_singleton():
    
    class TestSingleton(Singleton):
        pass

    with pytest.raises(TypeError):
        TestSingleton()