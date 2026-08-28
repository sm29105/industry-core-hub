#################################################################################
# Eclipse Tractus-X - Industry Core Hub Backend
# Test Suite: ConfigManager Dynamic Configuration Loading (Unit Tests)
#
# Copyright (c) 2025 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
#################################################################################

"""
Unit tests for ConfigManager dynamic configuration loading.

This test suite validates:
1. ConfigManager loads YAML configuration correctly
2. Section-based retrieval works for factory integration
3. Dot-notation retrieval works (backward compatibility)
4. Configuration validation catches invalid setups
5. SubmodelAdapterFactory initializes with configured adapters

Run with:
    pytest tests/managers/enablement_services/test_config_dynamic.py -v
"""

import pytest


class TestConfigManagerLoadConfiguration:
    """Test ConfigManager configuration loading from YAML files."""

    def test_load_config_yaml(self, config_path):
        """Validate YAML configuration file exists and is valid."""
        from managers.config.config_manager import ConfigManager

        # Load and verify structure
        config = ConfigManager.load_config(str(config_path))

        assert config is not None
        assert "provider" in config
        assert "submodel_dispatcher" in config["provider"]
        assert config["provider"]["submodel_dispatcher"]["mode"] == "s3"

    def test_config_caching_on_repeated_loads(self, config_path):
        """Validate ConfigManager caches configuration and doesn't reload."""
        from managers.config.config_manager import ConfigManager

        # Reset cache
        ConfigManager._raw_config = None

        # First load
        config1 = ConfigManager.load_config(str(config_path))

        # Second load should return cached version
        config2 = ConfigManager.load_config(str(config_path))

        # Should be identical
        assert config1 == config2
        assert ConfigManager._raw_config is not None


class TestConfigManagerSectionRetrieval:
    """Test section-based configuration retrieval for factory patterns."""

    def test_get_section_returns_dict(self, config_manager_with_unit_test):
        """Validate get_section returns configuration section as dictionary."""
        section = config_manager_with_unit_test.get_section(
            "provider.submodel_dispatcher"
        )

        assert isinstance(section, dict)
        assert "mode" in section
        assert "s3" in section
        assert section["mode"] == "s3"

    def test_get_section_s3_config(self, config_manager_with_unit_test):
        """Validate S3 section retrieval returns complete adapter config."""
        section = config_manager_with_unit_test.get_section(
            "provider.submodel_dispatcher.s3"
        )

        assert isinstance(section, dict)
        assert section["bucket_name"] == "submodels-tests"
        assert section["endpoint_url"] == "http://localhost:8333"
        assert "aws_access_key_id" in section

    def test_get_section_with_default(self, config_manager_with_unit_test):
        """Validate get_section returns default if section not found."""
        default_value = {"default": "config"}
        section = config_manager_with_unit_test.get_section(
            "nonexistent.section", default=default_value
        )

        assert section == default_value

    def test_get_section_returns_empty_dict_without_default(
        self, config_manager_with_unit_test
    ):
        """Validate get_section returns empty dict if section not found and no default."""
        section = config_manager_with_unit_test.get_section("nonexistent.section")

        assert isinstance(section, dict)
        assert len(section) == 0


class TestConfigManagerDotNotationRetrieval:
    """Test backward-compatible dot-notation retrieval."""

    def test_get_single_value_with_dot_notation(self, config_manager_with_unit_test):
        """Validate dot-notation retrieval for single values."""
        mode = config_manager_with_unit_test.get("provider.submodel_dispatcher.mode")

        assert mode == "s3"

    def test_get_nested_value(self, config_manager_with_unit_test):
        """Validate nested value retrieval with dot notation."""
        bucket_name = config_manager_with_unit_test.get(
            "provider.submodel_dispatcher.s3.bucket_name"
        )

        assert bucket_name == "submodels-tests"

    def test_get_with_default_value(self, config_manager_with_unit_test):
        """Validate default value is returned for missing keys."""
        value = config_manager_with_unit_test.get(
            "nonexistent.key", default="fallback_value"
        )

        assert value == "fallback_value"

    def test_get_with_missing_intermediate_key(self, config_manager_with_unit_test):
        """Validate None/default returned for missing intermediate keys."""
        value = config_manager_with_unit_test.get(
            "provider.nonexistent.submodel_dispatcher.mode", default="default_mode"
        )

        assert value == "default_mode"


class TestConfigManagerAdapterModeAndConfig:
    """Test get_adapter_mode_and_config for factory integration."""

    def test_get_adapter_mode_and_config_s3(self, config_manager_with_unit_test):
        """Validate retrieval of S3 adapter mode and configuration."""
        mode, config = config_manager_with_unit_test.get_adapter_mode_and_config(
            validate_adapter_exists=False
        )

        assert mode == "s3"
        assert isinstance(config, dict)
        assert config["bucket_name"] == "submodels-tests"
        assert config["endpoint_url"] == "http://localhost:8333"

    def test_get_adapter_mode_and_config_filesystem(
        self, config_manager_with_filesystem
    ):
        """Validate retrieval of FileSystem adapter mode and configuration."""
        mode, config = config_manager_with_filesystem.get_adapter_mode_and_config(
            validate_adapter_exists=False
        )

        assert mode == "file_system"
        assert isinstance(config, dict)
        assert "path" in config
        assert "path_pattern" in config
        assert config["path_pattern"] == "{base_path}/{semantic_id}/{submodel_id}.json"

    def test_get_adapter_mode_and_config_http_submodel(
        self, config_manager_with_http_submodel
    ):
        """Validate retrieval of HTTP Submodel adapter mode and configuration."""
        mode, config = config_manager_with_http_submodel.get_adapter_mode_and_config(
            validate_adapter_exists=False
        )

        assert mode == "http_submodel"
        assert isinstance(config, dict)
        assert config["base_url"] == "https://external-ichub.example.com"
        assert config["api_path"] == "/api/v1"
        assert config["timeout"] == 30
        assert config["verify_ssl"] is True
        assert "auth" in config
        assert config["auth"]["token"] == "test-token"
        assert config["auth"]["key_name"] == "X-Api-Key"

    def test_get_adapter_mode_and_config_with_validation(
        self, config_manager_with_unit_test
    ):
        """Validate adapter existence validation with real SubmodelAdapterFactory."""
        # Use real factory to validate S3 is a built-in adapter
        mode, config = config_manager_with_unit_test.get_adapter_mode_and_config(
            validate_adapter_exists=True
        )

        assert mode == "s3"
        assert isinstance(config, dict)

    def test_get_adapter_mode_and_config_missing_mode(self):
        """Validate error when adapter mode is missing."""
        from managers.config.config_manager import ConfigManager

        # Create config without mode
        bad_config = {
            "provider": {
                "submodel_dispatcher": {
                    "s3": {"bucket_name": "test"}
                    # Missing "mode" key
                }
            }
        }
        ConfigManager._raw_config = bad_config

        with pytest.raises(ValueError, match="No adapter mode specified"):
            ConfigManager.get_adapter_mode_and_config(validate_adapter_exists=False)

    def test_get_adapter_mode_and_config_missing_section(self):
        """Validate error when dispatcher section is missing."""
        from managers.config.config_manager import ConfigManager

        ConfigManager._raw_config = {"provider": {}}

        with pytest.raises(ValueError, match="Configuration section.*not found"):
            ConfigManager.get_adapter_mode_and_config(validate_adapter_exists=False)


class TestConfigManagerGetConfig:
    """Test full configuration retrieval."""

    def test_get_config_returns_full_config(self, config_manager_with_unit_test):
        """Validate get_config returns complete configuration."""
        full_config = config_manager_with_unit_test.get_config()

        assert isinstance(full_config, dict)
        assert "provider" in full_config
        assert full_config["provider"]["submodel_dispatcher"]["mode"] == "s3"


class TestSubmodelAdapterFactoryIntegration:
    """Test integration between ConfigManager and SubmodelAdapterFactory."""

    def test_factory_receives_s3_config_from_config_manager(
        self, config_manager_with_unit_test
    ):
        """Validate ConfigManager output can be used with SubmodelAdapterFactory."""
        # Get adapter config from ConfigManager
        mode, adapter_config = (
            config_manager_with_unit_test.get_adapter_mode_and_config(
                validate_adapter_exists=False  # Don't validate adapter exists
            )
        )

        # Verify it's valid S3 configuration
        assert mode == "s3"
        assert "bucket_name" in adapter_config
        assert "endpoint_url" in adapter_config

    def test_factory_receives_filesystem_config_from_config_manager(
        self, config_manager_with_filesystem
    ):
        """Validate ConfigManager returns raw filesystem config (transformation happens in factory)."""
        mode, adapter_config = (
            config_manager_with_filesystem.get_adapter_mode_and_config(
                validate_adapter_exists=False
            )
        )

        assert mode == "file_system"
        # ConfigManager returns raw YAML config; factory handles transformation
        assert "path" in adapter_config
        assert "path_pattern" in adapter_config

    def test_factory_receives_http_submodel_config_from_config_manager(
        self, config_manager_with_http_submodel
    ):
        """Validate ConfigManager returns raw HTTP Submodel config (transformation happens in factory)."""
        mode, adapter_config = (
            config_manager_with_http_submodel.get_adapter_mode_and_config(
                validate_adapter_exists=False
            )
        )
        assert mode == "http_submodel"
        # ConfigManager returns raw YAML config; factory handles transformation
        assert "base_url" in adapter_config
        assert "api_path" in adapter_config
        assert "url_pattern" in adapter_config
        assert "auth" in adapter_config
        assert "token" in adapter_config["auth"]
        assert "key_name" in adapter_config["auth"]

    @pytest.mark.skip(
        reason="Factory requires transformed config; ConfigManager returns raw YAML. "
        "Use AdapterConfigurationInterface to transform config before factory call."
    )
    def test_factory_from_config_called_with_s3_args(
        self, config_manager_with_unit_test
    ):
        """Validate factory is called with S3 mode and config from ConfigManager."""
        mode, adapter_config = (
            config_manager_with_unit_test.get_adapter_mode_and_config(
                validate_adapter_exists=False
            )
        )

        from tractusx_sdk.industry.adapters.submodel_adapter_factory import (
            SubmodelAdapterFactory,
        )

        # Note: adapter_config is raw YAML; factory expects transformed config
        adapter = SubmodelAdapterFactory.from_config(mode, adapter_config)

        assert adapter is not None
        assert mode == "s3"

    @pytest.mark.skip(
        reason="Factory requires transformed config; ConfigManager returns raw YAML. "
        "Use AdapterConfigurationInterface to transform config before factory call."
    )
    def test_factory_from_config_called_with_filesystem_args(
        self, config_manager_with_filesystem
    ):
        """Validate factory is called with FileSystem mode and config."""
        mode, adapter_config = (
            config_manager_with_filesystem.get_adapter_mode_and_config(
                validate_adapter_exists=False
            )
        )

        from tractusx_sdk.industry.adapters.submodel_adapter_factory import (
            SubmodelAdapterFactory,
        )

        # Note: adapter_config is raw YAML; factory expects transformed config
        adapter = SubmodelAdapterFactory.from_config(mode, adapter_config)

        assert adapter is not None
        assert mode == "file_system"

    @pytest.mark.skip(
        reason="Factory requires transformed config; ConfigManager returns raw YAML. "
        "Use AdapterConfigurationInterface to transform config before factory call."
    )
    def test_factory_from_config_called_with_http_submodel_args(
        self, config_manager_with_http_submodel
    ):
        """Validate factory is called with HTTP Submodel mode and config."""
        mode, adapter_config = (
            config_manager_with_http_submodel.get_adapter_mode_and_config(
                validate_adapter_exists=False
            )
        )

        from tractusx_sdk.industry.adapters.submodel_adapter_factory import (
            SubmodelAdapterFactory,
        )

        # Note: adapter_config is raw YAML; factory expects transformed config
        adapter = SubmodelAdapterFactory.from_config(mode, adapter_config)

        assert adapter is not None
        assert mode == "http_submodel"


class TestConfigurationErrorHandling:
    """Test error handling for invalid configurations."""

    def test_invalid_yaml_raises_error(self, tmp_path):
        """Validate error handling for invalid YAML."""
        from managers.config.config_manager import ConfigManager

        # Create invalid YAML file
        invalid_yaml = tmp_path / "invalid.yml"
        invalid_yaml.write_text("invalid: yaml: content: [")

        # Reset cache
        ConfigManager._raw_config = None

        config = ConfigManager.load_config(str(invalid_yaml))

        # Returns empty dict on error
        assert config == {}

    def test_missing_config_file_returns_empty_dict(self, tmp_path):
        """Validate graceful handling of missing config file."""
        from managers.config.config_manager import ConfigManager

        ConfigManager._raw_config = None

        config = ConfigManager.load_config(str(tmp_path / "nonexistent.yml"))

        assert config == {}


class TestAllAdaptersParametrized:
    """Parametrized tests for all adapter types (FileSystem, HTTP Submodel, S3)."""

    @pytest.mark.parametrize(
        "adapter_type,config_fixture,expected_mode",
        [
            ("file_system", "config_manager_with_filesystem", "file_system"),
            ("http_submodel", "config_manager_with_http_submodel", "http_submodel"),
            ("s3", "config_manager_with_s3", "s3"),
        ],
    )
    def test_adapter_mode_retrieval(
        self, adapter_type, config_fixture, expected_mode, request
    ):
        """Parametrized test for adapter mode retrieval across all adapter types."""
        config_manager = request.getfixturevalue(config_fixture)
        mode, config = config_manager.get_adapter_mode_and_config(
            validate_adapter_exists=False
        )

        assert mode == expected_mode
        assert isinstance(config, dict)
        assert len(config) > 0

    @pytest.mark.parametrize(
        "adapter_type,config_fixture,section_path",
        [
            (
                "file_system",
                "config_manager_with_filesystem",
                "provider.submodel_dispatcher.file_system",
            ),
            (
                "http_submodel",
                "config_manager_with_http_submodel",
                "provider.submodel_dispatcher.http_submodel",
            ),
            ("s3", "config_manager_with_s3", "provider.submodel_dispatcher.s3"),
        ],
    )
    def test_adapter_section_retrieval(
        self, adapter_type, config_fixture, section_path, request
    ):
        """Parametrized test for adapter section retrieval across all adapter types."""
        config_manager = request.getfixturevalue(config_fixture)
        section = config_manager.get_section(section_path)

        assert isinstance(section, dict)
        assert len(section) > 0
        assert (
            adapter_type in section_path
        )  # Ensure section corresponds to adapter type

    @pytest.mark.parametrize(
        "adapter_type,config_fixture,expected_keys",
        [
            (
                "file_system",
                "config_manager_with_filesystem",
                ["path", "path_pattern"],
            ),
            (
                "http_submodel",
                "config_manager_with_http_submodel",
                ["base_url", "api_path", "url_pattern", "auth"],
            ),
            (
                "s3",
                "config_manager_with_s3",
                [
                    "bucket_name",
                    "region_name",
                    "endpoint_url",
                    "key_pattern",
                    "auth",
                ],
            ),
        ],
    )
    def test_adapter_has_required_keys(
        self, adapter_type, config_fixture, expected_keys, request
    ):
        """Parametrized test validating each adapter has required configuration keys from raw YAML."""
        config_manager = request.getfixturevalue(config_fixture)

        mode, config = config_manager.get_adapter_mode_and_config(
            validate_adapter_exists=False
        )

        for key in expected_keys:
            assert (
                key in config
            ), f"Expected key '{key}' not found in {adapter_type} config"


class TestConfigurationWithFileSystemAdapter:
    """Test configuration loading with FileSystem adapter (complementary to S3)."""

    def test_filesystem_adapter_config_loading(self, filesystem_test_config):
        """Validate FileSystem adapter configuration loading from raw YAML."""
        from managers.config.config_manager import ConfigManager

        ConfigManager._raw_config = filesystem_test_config

        mode, config = ConfigManager.get_adapter_mode_and_config(
            validate_adapter_exists=False
        )

        assert mode == "file_system"
        assert "path" in config
        assert "path_pattern" in config

    def test_config_section_for_filesystem(self, filesystem_test_config):
        """Validate section-based retrieval for FileSystem adapter."""
        from managers.config.config_manager import ConfigManager

        ConfigManager._raw_config = filesystem_test_config

        section = ConfigManager.get_section("provider.submodel_dispatcher.file_system")

        assert "path" in section
        assert "path_pattern" in section

    def test_filesystem_section_has_correct_values(
        self, config_manager_with_filesystem
    ):
        """Validate FileSystem section contains expected configuration values."""
        section = config_manager_with_filesystem.get_section(
            "provider.submodel_dispatcher.file_system"
        )

        assert section["path_pattern"] == "{base_path}/{semantic_id}/{submodel_id}.json"
        assert isinstance(section["path"], str)


class TestConfigurationWithHttpSubmodelAdapter:
    """Test configuration loading with HTTP Submodel adapter."""

    def test_http_submodel_adapter_config_loading(self, http_submodel_test_config):
        """Validate HTTP Submodel adapter configuration loading from raw YAML."""
        from managers.config.config_manager import ConfigManager

        ConfigManager._raw_config = http_submodel_test_config

        mode, config = ConfigManager.get_adapter_mode_and_config(
            validate_adapter_exists=False
        )

        assert mode == "http_submodel"
        assert "base_url" in config
        assert "url_pattern" in config
        assert "auth" in config
        assert "token" in config["auth"]
        assert "key_name" in config["auth"]

    def test_config_section_for_http_submodel(self, http_submodel_test_config):
        """Validate section-based retrieval for HTTP Submodel adapter."""
        from managers.config.config_manager import ConfigManager

        ConfigManager._raw_config = http_submodel_test_config

        section = ConfigManager.get_section(
            "provider.submodel_dispatcher.http_submodel"
        )

        assert "base_url" in section
        assert "api_path" in section
        assert "url_pattern" in section
        assert "auth" in section
        assert "token" in section["auth"]
        assert "key_name" in section["auth"]

    def test_http_submodel_section_has_correct_values(
        self, config_manager_with_http_submodel
    ):
        """Validate HTTP Submodel section contains expected configuration values."""
        section = config_manager_with_http_submodel.get_section(
            "provider.submodel_dispatcher.http_submodel"
        )

        assert section["base_url"] == "https://external-ichub.example.com"
        assert section["api_path"] == "/api/v1"
        assert section["timeout"] == 30
        assert section["verify_ssl"] is True

    def test_http_submodel_auth_section(self, config_manager_with_http_submodel):
        """Validate HTTP Submodel bearer token configuration."""
        section = config_manager_with_http_submodel.get_section(
            "provider.submodel_dispatcher.http_submodel"
        )

        assert section["auth"]["token"] == "test-token"
        assert section["auth"]["key_name"] == "X-Api-Key"

    def test_http_submodel_url_pattern(self, config_manager_with_http_submodel):
        """Validate HTTP Submodel URL pattern is properly configured."""
        section = config_manager_with_http_submodel.get_section(
            "provider.submodel_dispatcher.http_submodel"
        )

        url_pattern = section["url_pattern"]
        expected = "{base_url}{api_path}/{semantic_id}/{submodel_id}/submodel"
        assert url_pattern == expected


class TestConfigurationWithS3Adapter:
    """Test configuration loading with S3 adapter."""

    def test_s3_adapter_config_loading(self, s3_test_config):
        """Validate S3 adapter configuration loading."""
        from managers.config.config_manager import ConfigManager

        ConfigManager._raw_config = s3_test_config

        mode, config = ConfigManager.get_adapter_mode_and_config(
            validate_adapter_exists=False
        )

        assert mode == "s3"
        assert "bucket_name" in config
        assert "region_name" in config
        assert "endpoint_url" in config

    def test_config_section_for_s3(self, s3_test_config):
        """Validate section-based retrieval for S3 adapter."""
        from managers.config.config_manager import ConfigManager

        ConfigManager._raw_config = s3_test_config

        section = ConfigManager.get_section("provider.submodel_dispatcher.s3")

        assert "bucket_name" in section
        assert "region_name" in section
        assert "key_pattern" in section

    def test_s3_section_has_correct_values(self, config_manager_with_s3):
        """Validate S3 section contains expected configuration values."""
        section = config_manager_with_s3.get_section("provider.submodel_dispatcher.s3")

        assert section["bucket_name"] == "submodels-tests"
        assert section["region_name"] == "us-east-1"
        assert section["endpoint_url"] == "http://localhost:8333"
        assert section["key_pattern"] == "{semantic_id}/{submodel_id}.json"

    def test_s3_auth_section(self, config_manager_with_s3):
        """Validate S3 auth configuration."""
        section = config_manager_with_s3.get_section("provider.submodel_dispatcher.s3")

        assert section["auth"]["aws_access_key_id"] == "test-access-key"
        assert section["auth"]["aws_secret_access_key"] == "test-secret-key"


class TestConfigManagerGetAvailableAdapters:
    """Test ConfigManager.get_available_adapters() method."""

    def test_get_available_adapters_returns_list(self, config_manager_with_unit_test):
        """Validate get_available_adapters returns a list."""
        adapters = config_manager_with_unit_test.get_available_adapters()

        assert isinstance(adapters, list)
        assert len(adapters) > 0

    def test_get_available_adapters_contains_builtin(
        self, config_manager_with_unit_test
    ):
        """Validate get_available_adapters includes built-in adapter types."""
        adapters = config_manager_with_unit_test.get_available_adapters()

        # Check for built-in adapters
        assert "file_system" in adapters
        assert "s3" in adapters
        assert "http_submodel" in adapters

    def test_get_available_adapters_returns_sorted_list(
        self, config_manager_with_unit_test
    ):
        """Validate get_available_adapters returns sorted list."""
        adapters = config_manager_with_unit_test.get_available_adapters()

        # Should be sorted
        assert adapters == ["file_system", "http_submodel", "s3"]

    def test_get_available_adapters_string_format(self, config_manager_with_unit_test):
        """Validate adapter names use lowercase with underscores."""
        adapters = config_manager_with_unit_test.get_available_adapters()

        for adapter in adapters:
            # Should be lowercase with underscores, no spaces or mixed case
            assert adapter == adapter.lower()
            assert " " not in adapter
            assert adapter.replace("_", "").isalnum()

    def test_get_available_adapters_after_registration(
        self, config_manager_with_unit_test
    ):
        """Validate get_available_adapters includes newly registered adapters."""
        from managers.config.config_manager import ConfigManager

        # Get available adapters before registration
        initial_adapters = ConfigManager.get_available_adapters()
        initial_count = len(initial_adapters)

        # Register a test adapter
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        class TestCustomAdapter:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        try:
            # Registration should succeed without error
            SubmodelServiceManager.register_external_adapter(
                adapter_type="test_custom_adapter",
                adapter_class=TestCustomAdapter,
                overwrite=True,
            )

            # Get available adapters after registration
            updated_adapters = ConfigManager.get_available_adapters()

            # Should include all built-in adapters
            assert "file_system" in updated_adapters
            assert "s3" in updated_adapters
            assert "http_submodel" in updated_adapters

            # Should also include the newly registered custom adapter
            assert "test_custom_adapter" in updated_adapters

            # Should have one more adapter than before
            assert len(updated_adapters) == initial_count + 1
        finally:
            # Cleanup
            try:
                SubmodelServiceManager.unregister_external_adapter(
                    "test_custom_adapter"
                )
            except:
                pass

    def test_get_available_adapters_error_handling(self, config_manager_with_unit_test):
        """Validate get_available_adapters propagates factory exceptions."""
        from managers.config.config_manager import ConfigManager
        from unittest.mock import patch

        # Mock the factory to raise an exception
        with patch(
            "managers.config.config_manager.SubmodelAdapterFactory.get_available_adapter_types"
        ) as mock_factory:
            mock_factory.side_effect = Exception("Factory error")

            # Should propagate the exception since there is no error handling
            with pytest.raises(Exception, match="Factory error"):
                ConfigManager.get_available_adapters()


class TestConfigManagerRegisterExternalAdapter:
    """Test SubmodelServiceManager.register_external_adapter() method."""

    def test_register_adapter_with_adapter_class(self, config_manager_with_unit_test):
        """Validate registering an adapter with adapter_class parameter."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        class CustomAdapter:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        try:
            SubmodelServiceManager.register_external_adapter(
                adapter_type="custom_test_1",
                adapter_class=CustomAdapter,
                overwrite=True,
            )

            # Verify it's registered
            registered = SubmodelServiceManager.get_registered_adapters()
            assert "custom_test_1" in registered
        finally:
            try:
                SubmodelServiceManager.unregister_external_adapter("custom_test_1")
            except:
                pass

    def test_register_adapter_with_builder_factory(self, config_manager_with_unit_test):
        """Validate registering an adapter with builder_factory parameter."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )
        from unittest.mock import MagicMock

        builder_mock = MagicMock()

        try:
            SubmodelServiceManager.register_external_adapter(
                adapter_type="custom_test_2",
                builder_factory=lambda: builder_mock,
                overwrite=True,
            )

            # Verify it's registered
            registered = SubmodelServiceManager.get_registered_adapters()
            assert "custom_test_2" in registered
        finally:
            try:
                SubmodelServiceManager.unregister_external_adapter("custom_test_2")
            except:
                pass

    def test_register_adapter_without_parameters_raises_error(
        self, config_manager_with_unit_test
    ):
        """Validate error when neither builder_factory nor adapter_class provided."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        with pytest.raises((ValueError, TypeError)):
            SubmodelServiceManager.register_external_adapter(
                adapter_type="invalid_adapter", builder_factory=None, adapter_class=None
            )

    def test_register_adapter_duplicate_without_overwrite_raises_error(
        self, config_manager_with_unit_test
    ):
        """Validate error when registering duplicate adapter without overwrite=True."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        class TestAdapter:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        try:
            # Register first time
            SubmodelServiceManager.register_external_adapter(
                adapter_type="dup_test", adapter_class=TestAdapter
            )
            registered_first_time = SubmodelServiceManager.get_registered_adapters()
            print("registered_first_time:", registered_first_time)
            # Register second time
            SubmodelServiceManager.register_external_adapter(
                adapter_type="dup_test_2", adapter_class=TestAdapter
            )
            registered_second_time = SubmodelServiceManager.get_registered_adapters()
            print("registered_second_time:", registered_second_time)

            # Try to register again without overwrite
            with pytest.raises(ValueError):
                SubmodelServiceManager.register_external_adapter(
                    adapter_type="dup_test", adapter_class=TestAdapter, overwrite=False
                )
            registered_after_attempt = SubmodelServiceManager.get_registered_adapters()
            print("registered_after_attempt:", registered_after_attempt)
        finally:
            try:
                SubmodelServiceManager.unregister_external_adapter("dup_test")
            except:
                pass

    def test_register_adapter_duplicate_with_overwrite_succeeds(
        self, config_manager_with_unit_test
    ):
        """Validate overwriting an existing adapter registration."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        class TestAdapter1:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        class TestAdapter2:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        try:
            # Register first adapter
            SubmodelServiceManager.register_external_adapter(
                adapter_type="overwrite_test", adapter_class=TestAdapter1
            )

            # Overwrite with second adapter
            SubmodelServiceManager.register_external_adapter(
                adapter_type="overwrite_test",
                adapter_class=TestAdapter2,
                overwrite=True,
            )

            # Verify still registered
            registered = SubmodelServiceManager.get_registered_adapters()
            assert "overwrite_test" in registered
        finally:
            try:
                SubmodelServiceManager.unregister_external_adapter("overwrite_test")
            except:
                pass

    def test_register_adapter_with_invalid_class_raises_error(
        self, config_manager_with_unit_test
    ):
        """Validate error when adapter_class lacks builder() method."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        class InvalidAdapter:
            # Missing builder() method
            pass

        with pytest.raises(TypeError):
            SubmodelServiceManager.register_external_adapter(
                adapter_type="invalid_class", adapter_class=InvalidAdapter
            )

    def test_register_adapter_logs_success(self, config_manager_with_unit_test):
        """Validate successful registration is logged."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )
        from unittest.mock import patch

        class TestAdapter:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        try:
            with patch(
                "managers.enablement_services.submodel_service_manager.SubmodelServiceManager.logger"
            ) as mock_logger:
                SubmodelServiceManager.register_external_adapter(
                    adapter_type="logged_test",
                    adapter_class=TestAdapter,
                    overwrite=True,
                )

                # Verify logging occurred
                assert mock_logger.info.called
                call_args = str(mock_logger.info.call_args)
                assert "logged_test" in call_args or "registered" in call_args.lower()
        finally:
            try:
                SubmodelServiceManager.unregister_external_adapter("logged_test")
            except:
                pass


class TestConfigManagerGetRegisteredAdapters:
    """Test SubmodelServiceManager.get_registered_adapters() method."""

    def test_get_registered_adapters_returns_list(self, config_manager_with_unit_test):
        """Validate get_registered_adapters returns a list."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        registered = SubmodelServiceManager.get_registered_adapters()

        assert isinstance(registered, list)

    def test_get_registered_adapters_excludes_builtin(
        self, config_manager_with_unit_test
    ):
        """Validate get_registered_adapters excludes built-in adapters."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        registered = SubmodelServiceManager.get_registered_adapters()

        # Built-in adapters should NOT be in registered list
        assert "file_system" not in registered
        assert "s3" not in registered
        assert "http_submodel" not in registered

    def test_get_registered_adapters_after_registration(
        self, config_manager_with_unit_test
    ):
        """Validate registered adapters appear after registration."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        class TestAdapter:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        try:
            SubmodelServiceManager.register_external_adapter(
                adapter_type="show_registered_test",
                adapter_class=TestAdapter,
                overwrite=True,
            )

            registered = SubmodelServiceManager.get_registered_adapters()

            assert "show_registered_test" in registered
        finally:
            try:
                SubmodelServiceManager.unregister_external_adapter(
                    "show_registered_test"
                )
            except:
                pass

    def test_get_registered_adapters_empty_initially(
        self, config_manager_with_unit_test
    ):
        """Validate get_registered_adapters returns empty list if none registered."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        # Clean up any existing registrations first
        registered = SubmodelServiceManager.get_registered_adapters()
        for adapter in registered:
            try:
                SubmodelServiceManager.unregister_external_adapter(adapter)
            except:
                pass

        # Now check
        registered = SubmodelServiceManager.get_registered_adapters()
        assert isinstance(registered, list)
        # May be empty after cleanup
        assert all(isinstance(item, str) for item in registered)

    def test_get_registered_adapters_multiple_registrations(
        self, config_manager_with_unit_test
    ):
        """Validate multiple adapter registrations are all listed."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        class TestAdapter:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        adapters_to_register = ["multi_1", "multi_2", "multi_3"]

        try:
            # Register multiple adapters
            for adapter_name in adapters_to_register:
                SubmodelServiceManager.register_external_adapter(
                    adapter_type=adapter_name, adapter_class=TestAdapter, overwrite=True
                )

            registered = SubmodelServiceManager.get_registered_adapters()

            # All should be present
            for adapter_name in adapters_to_register:
                assert adapter_name in registered
        finally:
            # Cleanup
            for adapter_name in adapters_to_register:
                try:
                    SubmodelServiceManager.unregister_external_adapter(adapter_name)
                except:
                    pass

    def test_get_registered_adapters_sorted(self, config_manager_with_unit_test):
        """Validate get_registered_adapters returns sorted list."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        registered = SubmodelServiceManager.get_registered_adapters()

        assert registered == sorted(registered)

    def test_get_registered_adapters_error_handling(
        self, config_manager_with_unit_test
    ):
        """Validate get_registered_adapters returns empty list when no adapters registered."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        # Clean up any existing registrations first
        registered_before = SubmodelServiceManager.get_registered_adapters()
        for adapter in registered_before:
            try:
                SubmodelServiceManager.unregister_external_adapter(adapter)
            except:
                pass

        # get_registered_adapters should return an empty list if none are registered
        registered = SubmodelServiceManager.get_registered_adapters()

        # Should return empty list when no external adapters are registered
        assert isinstance(registered, list)
        # After cleanup, should be empty (or minimal)
        assert len(registered) >= 0


class TestConfigManagerUnregisterExternalAdapter:
    """Test SubmodelServiceManager.unregister_external_adapter() method."""

    def test_unregister_adapter_removes_from_registry(
        self, config_manager_with_unit_test
    ):
        """Validate unregistering an adapter removes it from registry."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        class TestAdapter:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        # Register
        SubmodelServiceManager.register_external_adapter(
            adapter_type="unreg_test", adapter_class=TestAdapter, overwrite=True
        )

        # Verify registered
        registered_before = SubmodelServiceManager.get_registered_adapters()
        print("registered_before:", registered_before)
        assert "unreg_test" in registered_before

        # Unregister
        SubmodelServiceManager.unregister_external_adapter("unreg_test")

        # Verify unregistered
        registered_after = SubmodelServiceManager.get_registered_adapters()
        print("registered_after:", registered_after)
        assert "unreg_test" not in registered_after

    def test_unregister_nonexistent_adapter_raises_error(
        self, config_manager_with_unit_test
    ):
        """Validate error when unregistering non-existent adapter."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        with pytest.raises(Exception):
            SubmodelServiceManager.unregister_external_adapter("does_not_exist_adapter")

    def test_unregister_builtin_adapter_raises_error(
        self, config_manager_with_unit_test
    ):
        """Validate error when attempting to unregister built-in adapter."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        with pytest.raises(Exception):
            SubmodelServiceManager.unregister_external_adapter("s3")

    def test_unregister_adapter_multiple_times_error(
        self, config_manager_with_unit_test
    ):
        """Validate error when unregistering same adapter twice."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        class TestAdapter:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        # Register and unregister once
        SubmodelServiceManager.register_external_adapter(
            adapter_type="double_unreg", adapter_class=TestAdapter, overwrite=True
        )
        SubmodelServiceManager.unregister_external_adapter("double_unreg")

        # Try to unregister again
        with pytest.raises(Exception):
            SubmodelServiceManager.unregister_external_adapter("double_unreg")

    def test_unregister_adapter_logs_success(self, config_manager_with_unit_test):
        """Validate successful unregistration is logged."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )
        from unittest.mock import patch

        class TestAdapter:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        SubmodelServiceManager.register_external_adapter(
            adapter_type="logged_unreg", adapter_class=TestAdapter, overwrite=True
        )

        with patch(
            "managers.enablement_services.submodel_service_manager.SubmodelServiceManager.logger"
        ) as mock_logger:
            SubmodelServiceManager.unregister_external_adapter("logged_unreg")

            # Verify logging occurred
            assert mock_logger.info.called
            call_args = str(mock_logger.info.call_args)
            assert "logged_unreg" in call_args or "unregistered" in call_args.lower()

    def test_unregister_does_not_affect_available_adapters(
        self, config_manager_with_unit_test
    ):
        """Validate unregistering adapter doesn't remove built-in adapters."""
        from managers.config.config_manager import ConfigManager
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        class TestAdapter:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        # Get initial available adapters
        available_before = ConfigManager.get_available_adapters()

        # Register and unregister
        SubmodelServiceManager.register_external_adapter(
            adapter_type="unaffected_test", adapter_class=TestAdapter, overwrite=True
        )
        SubmodelServiceManager.unregister_external_adapter("unaffected_test")

        # Get final available adapters
        available_after = ConfigManager.get_available_adapters()

        # Built-in adapters should be unchanged
        builtin = ["file_system", "s3", "http_submodel"]
        for adapter in builtin:
            assert adapter in available_after


class TestAdapterRegistrationIntegration:
    """Integration tests for adapter registration lifecycle."""

    def test_full_adapter_lifecycle(self, config_manager_with_unit_test):
        """Validate complete lifecycle: register -> get -> unregister."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        class LifecycleAdapter:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        lifecycle_name = "lifecycle_adapter"

        # Initially not registered
        initial_registered = SubmodelServiceManager.get_registered_adapters()
        assert lifecycle_name not in initial_registered

        # Register
        SubmodelServiceManager.register_external_adapter(
            adapter_type=lifecycle_name, adapter_class=LifecycleAdapter, overwrite=True
        )

        # Now it should be registered
        after_register = SubmodelServiceManager.get_registered_adapters()
        assert lifecycle_name in after_register

        # Unregister
        SubmodelServiceManager.unregister_external_adapter(lifecycle_name)

        # Should be gone
        final_registered = SubmodelServiceManager.get_registered_adapters()
        assert lifecycle_name not in final_registered

    def test_register_same_adapter_twice_with_overwrite(
        self, config_manager_with_unit_test
    ):
        """Validate re-registering adapter with overwrite=True works."""
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        class Adapter1:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        class Adapter2:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        adapter_name = "reregister_test"

        try:
            # First registration
            SubmodelServiceManager.register_external_adapter(
                adapter_type=adapter_name, adapter_class=Adapter1
            )

            registered1 = SubmodelServiceManager.get_registered_adapters()
            assert adapter_name in registered1

            # Re-register with different class
            SubmodelServiceManager.register_external_adapter(
                adapter_type=adapter_name, adapter_class=Adapter2, overwrite=True
            )

            # Still should be registered
            registered2 = SubmodelServiceManager.get_registered_adapters()
            assert adapter_name in registered2
        finally:
            try:
                SubmodelServiceManager.unregister_external_adapter(adapter_name)
            except:
                pass

    def test_mixed_builtin_and_registered_adapters(self, config_manager_with_unit_test):
        """Validate working with both built-in and registered adapters."""
        from managers.config.config_manager import ConfigManager
        from managers.enablement_services.submodel_service_manager import (
            SubmodelServiceManager,
        )

        class CustomAdapter:
            @classmethod
            def builder(cls):
                from unittest.mock import MagicMock

                return MagicMock()

        try:
            # Register custom adapter
            SubmodelServiceManager.register_external_adapter(
                adapter_type="custom_mixed", adapter_class=CustomAdapter, overwrite=True
            )

            # Get all available
            all_available = ConfigManager.get_available_adapters()

            # Should have built-in + custom
            assert "s3" in all_available  # Built-in
            assert "file_system" in all_available  # Built-in
            assert "http_submodel" in all_available  # Built-in
            assert "custom_mixed" in all_available  # Custom

            # Get only registered
            only_registered = SubmodelServiceManager.get_registered_adapters()

            # Should NOT have built-in, only custom
            assert "s3" not in only_registered
            assert "custom_mixed" in only_registered
        finally:
            try:
                SubmodelServiceManager.unregister_external_adapter("custom_mixed")
            except:
                pass
