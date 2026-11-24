import pytest

from models import JobPost
from rules import check_deal_breakers


def make_job(**overrides) -> JobPost:
    """A valid job with neutral defaults. Each test only sets what it checks."""
    fields = {
        "title": "Backend Engineer",
        "company": "Acme",
        "location": "Remote",
        "country": None,
        "work_mode": "remote",
        "open_to_bd": True,
        "visa_support": None,
        "relocation_support": None,
        "years_required": None,
        "must_haves": [],
        "nice_to_haves": [],
        "salary": None,
    }
    fields.update(overrides)
    return JobPost(**fields)


REMOTE_CLOSED = "Remote role not open to Bangladesh"
NO_SUPPORT = "Role outside Bangladesh without visa or relocation support"


@pytest.mark.parametrize(
    "overrides, expected",
    [
        # Remote: passes only if open_to_bd is True
        pytest.param({"work_mode": "remote", "open_to_bd": True}, [], id="remote-open"),
        pytest.param({"work_mode": "remote", "open_to_bd": False}, [REMOTE_CLOSED], id="remote-closed"),
        pytest.param({"work_mode": "remote", "open_to_bd": None}, [REMOTE_CLOSED], id="remote-null"),
        # Onsite abroad: passes if visa_support or relocation_support is True
        pytest.param({"work_mode": "onsite", "country": "Germany", "visa_support": True}, [], id="onsite-visa"),
        pytest.param({"work_mode": "onsite", "country": "Germany", "relocation_support": True}, [], id="onsite-reloc-only"),
        pytest.param(
            {"work_mode": "onsite", "country": "Germany", "visa_support": False, "relocation_support": True},
            [],
            id="onsite-no-visa-but-reloc",
        ),
        pytest.param({"work_mode": "onsite", "country": "Germany"}, [NO_SUPPORT], id="onsite-nothing"),
        pytest.param(
            {"work_mode": "onsite", "country": "Germany", "visa_support": False, "relocation_support": False},
            [NO_SUPPORT],
            id="onsite-both-false",
        ),
        # Hybrid is treated like onsite
        pytest.param({"work_mode": "hybrid", "country": "Germany"}, [NO_SUPPORT], id="hybrid-nothing"),
        # work_mode not stated (None) is treated like onsite
        pytest.param({"work_mode": None, "country": "Germany", "visa_support": True}, [], id="mode-null-visa"),
        pytest.param({"work_mode": None, "country": "Germany"}, [NO_SUPPORT], id="mode-null-nothing"),
        # Job based in Bangladesh: no visa or relocation needed
        pytest.param({"work_mode": "onsite", "country": "Bangladesh"}, [], id="onsite-in-bd"),
        pytest.param({"work_mode": "hybrid", "country": "Bangladesh"}, [], id="hybrid-in-bd"),
    ],
)
def test_deal_breakers(overrides, expected):
    job = make_job(**overrides)
    assert check_deal_breakers(job) == expected
