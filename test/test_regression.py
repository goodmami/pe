
import pytest

import pe


@pytest.mark.parametrize('parser', ['packrat', 'machine'])
def test_capture_choice(parser):
    assert pe.match(r'~("a" / "b" / "c")', 'c', parser=parser) is not None
    assert pe.match(r'~("a" / "b" / "c")', 'b', parser=parser) is not None
    assert pe.match(r'~("a" / "b" / "c")', 'a', parser=parser) is not None
