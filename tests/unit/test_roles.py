"""Unit tests for predefined roles."""

from copilot_council.roles.predefined import PREDEFINED_ROLES, get_role


class TestPredefinedRoles:
    """Tests for predefined role definitions."""

    def test_all_required_roles_exist(self) -> None:
        """All expected roles should be defined."""
        expected_roles = [
            "critic",
            "principal_engineer",
            "security_expert",
            "data_scientist",
            "product_manager",
            "devil_advocate",
            "synthesizer",
            "researcher",
        ]

        for role_name in expected_roles:
            assert role_name in PREDEFINED_ROLES, f"Missing role: {role_name}"

    def test_roles_have_required_fields(self) -> None:
        """All roles should have name, description, and system_prompt."""
        for name, role in PREDEFINED_ROLES.items():
            assert role.name == name
            assert role.description, f"Role {name} missing description"
            assert role.system_prompt, f"Role {name} missing system_prompt"

    def test_get_role_returns_role(self) -> None:
        """get_role should return the role by name."""
        role = get_role("critic")

        assert role is not None
        assert role.name == "critic"

    def test_get_role_case_insensitive(self) -> None:
        """get_role should be case-insensitive."""
        role = get_role("CRITIC")

        assert role is not None
        assert role.name == "critic"

    def test_get_role_unknown_returns_none(self) -> None:
        """get_role should return None for unknown roles."""
        role = get_role("nonexistent_role")

        assert role is None

    def test_security_expert_has_denied_tools(self) -> None:
        """Security expert should have default denied tools."""
        role = get_role("security_expert")

        assert role is not None
        assert len(role.default_denied_tools) > 0
        assert "shell(*)" in role.default_denied_tools
