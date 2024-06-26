import pytest
import sys

# Talon autoloads python files unless they start with "." and we want it to ignore the server directory
# Thus, we import this way since we can't import packages normally that start with a "."
sys.path.append(".atspi-server")
from lib import Singleton, InterruptableThread  # type: ignore

from shared.shared_types import ServerStatusResult, A11yElement


def test_singleton():
    class TestSingleton(Singleton):
        pass

    with pytest.raises(TypeError):
        TestSingleton()


def test_server_status_result():
    assert ServerStatusResult.generate_from("success") == ServerStatusResult.SUCCESS
    assert (
        ServerStatusResult.generate_from("noActionInterfaceError")
        == ServerStatusResult.NO_ACTION_INTERFACE_ERROR
    )


def test_thread():
    import time

    def dummy_fn():
        while True:
            if t.interrupted():
                break
            time.sleep(1)
        return 999

    start = time.time()
    t = InterruptableThread(target=dummy_fn, args=())
    t.start()
    t.interrupt()
    result = t.join()
    assert t.interrupted() is True
    assert result == 999
    end = time.time()
    assert end - start < 2


def test_serialization():
    elem = A11yElement("test", 0, 0, "test", 0)
    dict_representation = elem.to_dict()

    assert A11yElement.from_dict(dict_representation) == elem
    assert dict_representation == {
        "name": "test",
        "x": 0,
        "y": 0,
        "role": "test",
        "pid": 0,
    }


# payload = '{"command": "click", "target": {"name": "TERMINAL", "x": 623, "y": 774, "role": "static", "pid": 3740}}'
