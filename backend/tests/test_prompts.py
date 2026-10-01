"""
Unit tests for src/prompts.py
Pure unit tests — no database, no network required.
Run: pytest tests/test_prompts.py -v
"""
import pytest
import yaml
import src.prompts as prompts


# ── get_system_prompt ─────────────────────────────────────────────────────────

class TestGetSystemPrompt:

    def test_general_role_returns_general_prompt(self):
        result = prompts.get_system_prompt('general')
        assert result is not None
        assert 'home user' in result.lower()

    def test_admin_role_returns_technical_prompt(self):
        result = prompts.get_system_prompt('admin')
        assert result is not None
        # Technical prompt mentions engineer or admin users
        assert 'engineer' in result.lower() or 'admin' in result.lower()

    def test_engineer_role_returns_technical_prompt(self):
        result = prompts.get_system_prompt('engineer')
        assert result is not None
        assert 'engineer' in result.lower() or 'admin' in result.lower()

    def test_unknown_role_returns_general_prompt(self):
        result = prompts.get_system_prompt('unknown_role')
        assert result is not None
        assert 'home user' in result.lower()

    def test_prompt_is_non_empty_string(self):
        assert isinstance(prompts.get_system_prompt('general'), str)
        assert len(prompts.get_system_prompt('general')) > 50


# ── get_max_tokens ────────────────────────────────────────────────────────────

class TestGetMaxTokens:

    def test_general_role_returns_300(self):
        assert prompts.get_max_tokens('general') == 300

    def test_admin_role_returns_700(self):
        assert prompts.get_max_tokens('admin') == 700

    def test_engineer_role_returns_700(self):
        assert prompts.get_max_tokens('engineer') == 700

    def test_context_command_returns_700_for_general(self):
        assert prompts.get_max_tokens('general', is_ctx_cmd=True) == 700

    def test_context_command_returns_700_for_admin(self):
        assert prompts.get_max_tokens('admin', is_ctx_cmd=True) == 700

    def test_returns_integer(self):
        assert isinstance(prompts.get_max_tokens('general'), int)


# ── get_all ───────────────────────────────────────────────────────────────────

class TestGetAll:

    def test_returns_dict(self):
        config = prompts.get_all()
        assert isinstance(config, dict)

    def test_has_all_sections(self):
        config = prompts.get_all()
        assert 'general' in config
        assert 'technical' in config
        assert 'context_commands' in config

    def test_general_section_has_system_and_max_tokens(self):
        config = prompts.get_all()
        assert 'system' in config['general']
        assert 'max_tokens' in config['general']

    def test_technical_section_has_system_and_max_tokens(self):
        config = prompts.get_all()
        assert 'system' in config['technical']
        assert 'max_tokens' in config['technical']

    def test_context_commands_has_max_tokens(self):
        config = prompts.get_all()
        assert 'max_tokens' in config['context_commands']

    def test_returns_independent_copy(self):
        config1 = prompts.get_all()
        config2 = prompts.get_all()
        config1['general']['max_tokens'] = 9999
        assert config2['general']['max_tokens'] != 9999


# ── save & reload ─────────────────────────────────────────────────────────────

class TestSaveAndReload:

    def test_save_persists_max_tokens(self, tmp_path):
        original_path = prompts._YAML_PATH
        test_yaml = tmp_path / "prompts.yaml"
        prompts._YAML_PATH = test_yaml

        try:
            data = prompts.get_all()
            data['general']['max_tokens'] = 123
            prompts.save(data)

            prompts._loaded = {}
            prompts.reload()
            assert prompts.get_max_tokens('general') == 123
        finally:
            prompts._YAML_PATH = original_path
            prompts.reload()

    def test_save_persists_system_prompt(self, tmp_path):
        original_path = prompts._YAML_PATH
        test_yaml = tmp_path / "prompts.yaml"
        prompts._YAML_PATH = test_yaml

        try:
            data = prompts.get_all()
            data['general']['system'] = 'Custom test prompt.'
            prompts.save(data)

            prompts._loaded = {}
            prompts.reload()
            assert prompts.get_system_prompt('general') == 'Custom test prompt.'
        finally:
            prompts._YAML_PATH = original_path
            prompts.reload()

    def test_reload_from_missing_file_uses_defaults(self, tmp_path):
        original_path = prompts._YAML_PATH
        prompts._YAML_PATH = tmp_path / "nonexistent.yaml"

        try:
            prompts._loaded = {}
            prompts.reload()
            assert prompts.get_max_tokens('general') == 300
            assert 'home user' in prompts.get_system_prompt('general').lower()
        finally:
            prompts._YAML_PATH = original_path
            prompts.reload()

    def test_yaml_file_written_is_valid_yaml(self, tmp_path):
        original_path = prompts._YAML_PATH
        test_yaml = tmp_path / "prompts.yaml"
        prompts._YAML_PATH = test_yaml

        try:
            prompts.save(prompts.get_all())
            with open(test_yaml, encoding='utf-8') as f:
                parsed = yaml.safe_load(f)
            assert isinstance(parsed, dict)
            assert 'general' in parsed
        finally:
            prompts._YAML_PATH = original_path
            prompts.reload()
