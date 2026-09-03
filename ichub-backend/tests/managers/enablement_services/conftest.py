#################################################################################
# Eclipse Tractus-X - Industry Core Hub Backend
#
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

import pytest
import yaml
import sys
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock

@pytest.fixture(scope="session")
def config_path() -> Path:
    """
    Provide path test configuration file.
    
    Returns:
        Path object pointing to configuration.yml
    """
    test_dir = Path(__file__).parent
    config_path = test_dir / "config" / "configuration.yml"
    if not config_path.exists():
        pytest.skip(f"Config file not found at {config_path}")
    return config_path


@pytest.fixture(scope="session")
def filesystem_config_path() -> Path:
    """
    Provide path to FileSystem test configuration file.
    
    Returns:
        Path object pointing to configuration-filesystem.yml
    """
    test_dir = Path(__file__).parent
    config_path = test_dir / "config" / "configuration-filesystem.yml"
    if not config_path.exists():
        pytest.skip(f"Config file not found at {config_path}")
    return config_path


@pytest.fixture(scope="session")
def http_submodel_config_path() -> Path:
    """
    Provide path to HTTP Submodel test configuration file.
    
    Returns:
        Path object pointing to configuration-http-submodel.yml
    """
    test_dir = Path(__file__).parent
    config_path = test_dir / "config" / "configuration-http-submodel.yml"
    if not config_path.exists():
        pytest.skip(f"Config file not found at {config_path}")
    return config_path


@pytest.fixture(scope="session")
def s3_config_path() -> Path:
    """
    Provide path to S3 test configuration file.
    
    Returns:
        Path object pointing to configuration-s3.yml
    """
    test_dir = Path(__file__).parent
    config_path = test_dir / "config" / "configuration-s3.yml"
    if not config_path.exists():
        pytest.skip(f"Config file not found at {config_path}")
    return config_path


@pytest.fixture(scope="session")
def test_config(config_path: Path) -> Dict[str, Any]:
    """
    Load test configuration from YAML file.
    
    Yields:
        Dictionary containing test configuration
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config



@pytest.fixture(scope="function")
def config_manager_with_seaweedfs(test_config):
    """
    Provide ConfigManager with test configuration loaded.
    
    This fixture:
    1. Mocks ConfigManager._raw_config with test config
    2. Allows testing dynamic config retrieval without file I/O
    
    Yields:
        ConfigManager class ready for testing
    """
    from managers.config.config_manager import ConfigManager
    
    # Store original value
    original_config = ConfigManager._raw_config
    
    # Set test config
    ConfigManager._raw_config = test_config
    
    yield ConfigManager
    
    # Restore original config
    ConfigManager._raw_config = original_config


@pytest.fixture(scope="function")
def config_manager_with_unit_test(test_config):
    """
    Provide ConfigManager with unit test configuration loaded.
    
    Alias for config_manager_with_seaweedfs for test compatibility.
    This fixture injects test configuration into ConfigManager without file I/O.
    
    The global SDK mock is disabled by the disable_global_sdk_mock fixture,
    so SubmodelAdapterFactory works with the real SDK implementation.
    
    Yields:
        ConfigManager class ready for testing
    """
    from managers.config.config_manager import ConfigManager
    
    # Store original value
    original_config = ConfigManager._raw_config
    
    # Set test config
    ConfigManager._raw_config = test_config
    
    yield ConfigManager
    
    # Restore original config
    ConfigManager._raw_config = original_config


@pytest.fixture(scope="function")
def filesystem_test_config(filesystem_config_path: Path) -> Dict[str, Any]:
    """
    Load FileSystem adapter test configuration from YAML file.
    
    Args:
        filesystem_config_path: Path to configuration-filesystem.yml
    
    Returns:
        Dictionary containing FileSystem adapter configuration
    """
    with open(filesystem_config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


@pytest.fixture(scope="function")
def http_submodel_test_config(http_submodel_config_path: Path) -> Dict[str, Any]:
    """
    Load HTTP Submodel adapter test configuration from YAML file.
    
    Args:
        http_submodel_config_path: Path to configuration-http-submodel.yml
    
    Returns:
        Dictionary containing HTTP Submodel adapter configuration
    """
    with open(http_submodel_config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


@pytest.fixture(scope="function")
def s3_test_config(s3_config_path: Path) -> Dict[str, Any]:
    """
    Load S3 adapter test configuration from YAML file.
    
    Args:
        s3_config_path: Path to configuration-s3.yml
    
    Returns:
        Dictionary containing S3 adapter configuration
    """
    with open(s3_config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


@pytest.fixture(scope="function")
def config_manager_with_filesystem(filesystem_test_config) -> Any:
    """
    Provide ConfigManager with filesystem test configuration loaded.
    
    Args:
        filesystem_test_config: FileSystem test configuration fixture
    
    Yields:
        ConfigManager class with filesystem configuration
    """
    from managers.config.config_manager import ConfigManager
    
    original_config = ConfigManager._raw_config
    ConfigManager._raw_config = filesystem_test_config
    
    yield ConfigManager
    
    ConfigManager._raw_config = original_config


@pytest.fixture(scope="function")
def config_manager_with_http_submodel(http_submodel_test_config) -> Any:
    """
    Provide ConfigManager with HTTP submodel test configuration loaded.
    
    Args:
        http_submodel_test_config: HTTP Submodel test configuration fixture
    
    Yields:
        ConfigManager class with HTTP submodel configuration
    """
    from managers.config.config_manager import ConfigManager
    
    original_config = ConfigManager._raw_config
    ConfigManager._raw_config = http_submodel_test_config
    
    yield ConfigManager
    
    ConfigManager._raw_config = original_config


@pytest.fixture(scope="function")
def config_manager_with_s3(s3_test_config) -> Any:
    """
    Provide ConfigManager with S3 test configuration loaded.
    
    Args:
        s3_test_config: S3 test configuration fixture
    
    Yields:
        ConfigManager class with S3 configuration
    """
    from managers.config.config_manager import ConfigManager
    
    original_config = ConfigManager._raw_config
    ConfigManager._raw_config = s3_test_config
    
    yield ConfigManager
