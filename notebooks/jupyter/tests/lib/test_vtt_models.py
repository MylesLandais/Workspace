"""Tests for lib.vtt.models module."""

from lib.vtt.models.character import AbilityScores


class TestAbilityScores:
    """Test D&D ability scores model."""

    def test_create_with_defaults(self):
        scores = AbilityScores(
            strength=10, dexterity=10, constitution=10,
            intelligence=10, wisdom=10, charisma=10,
        )
        assert scores.strength == 10

    def test_to_dict(self):
        scores = AbilityScores(
            strength=18, dexterity=14, constitution=16,
            intelligence=12, wisdom=13, charisma=8,
        )
        d = scores.to_dict()
        assert d["str"] == 18
        assert d["dex"] == 14
        assert d["cha"] == 8

    def test_from_dict_short_keys(self):
        data = {"str": 20, "dex": 15, "con": 14, "int": 10, "wis": 12, "cha": 8}
        scores = AbilityScores.from_dict(data)
        assert scores.strength == 20
        assert scores.charisma == 8

    def test_from_dict_long_keys(self):
        data = {
            "strength": 16, "dexterity": 14, "constitution": 12,
            "intelligence": 10, "wisdom": 13, "charisma": 11,
        }
        scores = AbilityScores.from_dict(data)
        assert scores.strength == 16

    def test_validation_rejects_out_of_range(self):
        import pytest
        with pytest.raises(Exception):
            AbilityScores(
                strength=0, dexterity=10, constitution=10,
                intelligence=10, wisdom=10, charisma=10,
            )

    def test_validation_rejects_over_30(self):
        import pytest
        with pytest.raises(Exception):
            AbilityScores(
                strength=31, dexterity=10, constitution=10,
                intelligence=10, wisdom=10, charisma=10,
            )
