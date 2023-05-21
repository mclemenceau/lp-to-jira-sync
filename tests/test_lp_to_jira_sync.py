#####################################################################
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
from lp_to_jira_sync.lp_to_jira_sync import \
    get_bug_id, get_bug_pkg


def test_get_bug_id():
    assert get_bug_id(None) == ""
    assert get_bug_id("") == ""
    assert get_bug_id("This isn't the right title") == ""
    assert get_bug_id("LP#123234") == "123234"
    assert get_bug_id("LP#123234 [busybox] There is a problemm") == "123234"
    assert get_bug_id("LP# 123234 [busybox] There is a problemm") == ""
    assert get_bug_id("Review LP#123234 [busybox] There is a problemm") == "123234"

def test_get_bug_pkg():
    assert get_bug_pkg(None) == ""
    assert get_bug_pkg("") == ""
    assert get_bug_pkg("This isn't the right title") == ""
    assert get_bug_pkg("LP#123234") == ""
    assert get_bug_pkg("LP#123234 [busybox] There is a problemm") == "busybox"
    assert get_bug_pkg("LP# 123234 [busybox] There is a problemm") == "busybox"
