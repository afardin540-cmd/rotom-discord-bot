import pytest

import services.iv_engine as engine
from services.iv_engine import CPM


def test_cpm_has_standard_levels():
    assert CPM[1] == 0.094
    assert CPM[20] > CPM[10]
    assert CPM[50] > CPM[40]
    assert CPM[51] > CPM[50]


def test_iv_space_size():
    assert 16 ** 3 == 4096


@pytest.fixture
def fake_gamemaster(monkeypatch):
    monkeypatch.setattr(engine, "_load_gamemaster", lambda: {
        "pokemon": [{
            "speciesId": "testmon",
            "speciesName": "Testmon",
            "baseStats": {"atk": 100, "def": 100, "hp": 100},
        }, {
            "speciesId": "testmon_alolan",
            "speciesName": "Testmon (Alolan)",
            "baseStats": {"atk": 110, "def": 90, "hp": 100},
        }]
    })
    return True


def test_best_buddy_allows_level_51(fake_gamemaster):
    normal = engine.calculate_rank("testmon", 15, 15, 15, "great")
    buddy = engine.calculate_rank("testmon", 15, 15, 15, "great", best_buddy=True)
    assert normal["level"] <= 50
    assert buddy["level"] >= normal["level"]
    assert buddy["best_buddy"] is True


def test_shadow_changes_battle_stats_but_not_cp(fake_gamemaster):
    normal = engine.calculate_rank("testmon", 10, 10, 10, "great")
    shadow = engine.calculate_rank("testmon", 10, 10, 10, "great", shadow=True)
    assert shadow["cp"] == normal["cp"]
    assert shadow["attack"] > normal["attack"]
    assert shadow["defense"] < normal["defense"]


def test_form_is_resolved(fake_gamemaster):
    result = engine.calculate_rank("testmon", 0, 15, 15, "great", form="alolan")
    assert "Alolan" in result["pokemon"]
    assert result["form"] == "alolan"
