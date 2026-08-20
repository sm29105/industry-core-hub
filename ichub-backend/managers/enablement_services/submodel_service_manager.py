#################################################################################
# Eclipse Tractus-X - Industry Core Hub Backend
#
# Copyright (c) 2026 LKS Next
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
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

from dataclasses import dataclass
from typing import Dict, Any, Callable
from uuid import UUID
from hashlib import sha256
from enum import Enum

from managers.config.config_manager import ConfigManager
from managers.config.log_manager import LoggingManager
from tools.exceptions import InvalidError, NotFoundError

from tractusx_sdk.industry.adapters import SubmodelAdapter
from tractusx_sdk.industry.adapters.submodel_adapter_factory import SubmodelAdapterFactory
from managers.enablement_services.adapters.adapter_config_manager import AdapterConfigurationInterface


class OperationType(Enum):
    """Enumeration of supported submodel operations."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"


@dataclass
class SubmodelMetadata:
    """
    Container for submodel metadata used across read/write/delete operations.
    
    Attributes:
        submodel_id: UUID of the submodel.
        semantic_id: Semantic ID of the submodel.
        semantic_id_hash: SHA-256 hash of the semantic ID for storage organization.
    """
    submodel_id: str
    semantic_id: str
    semantic_id_hash: str
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert metadata to dictionary for adapter operations.
        
        Returns:
            Dictionary representation of metadata.
        """
        return {
            "submodel_id": self.submodel_id,
            "semantic_id": self.semantic_id,
            "semantic_id_hash": self.semantic_id_hash,
        }

class SubmodelServiceManager:
    """
    Manager for handling submodel service operations (read, write, delete).
    
    Uses lazy initialization to ensure efficient adapter creation and configuration.
    Features 100% dynamic adapter initialization based on configuration via SubmodelAdapterFactory.
    Supports multiple storage backends:
    - FileSystem (local storage)
    - S3 (AWS S3 or S3-compatible)
    - HttpSubmodel (external submodel service)
    
    Singleton Pattern Infrastructure:
    The singleton pattern infrastructure (__new__ method) is prepared but not currently enforced.
    This allows flexibility for potential future use. Currently, lazy initialization via __init__
    is used to initialize the adapter only once per application runtime.
    
    Configuration is loaded from YAML and passed to the factory without any hardcoded logic
    or switch statements. Adapter type and configuration are determined dynamically from
    the configuration section: provider.submodel_dispatcher
    
    Example:
        # Initialize adapter from configuration
        manager = SubmodelServiceManager()
        
        # Subsequent instantiations initialize the same way (due to lazy initialization)
        manager2 = SubmodelServiceManager()
        # Both reference the same initialized adapter instance
    """
    _instance = None
    _initialized = False
    _external_adapters: Dict[str, Any] = {}  # Track registered external adapters
    logger = LoggingManager.get_logger(__name__)
    
    # def __new__(cls):
    #     """
    #     Implement singleton pattern to ensure only one adapter instance exists.
        
    #     Creates a single instance on first instantiation and initializes the _initialized
    #     flag for lazy initialization. Subsequent calls return the existing instance.
        
    #     Returns:
    #         Singleton instance of SubmodelServiceManager.
    #     """
    #     if cls._instance is None:
    #         cls._instance = super().__new__(cls)
    #         cls._instance._initialized = False
    #     return cls._instance

    def __init__(self):
        """
        Initialize SubmodelServiceManager with lazy initialization pattern.
        
        Implements lazy initialization to create the adapter instance only once during
        application runtime. The _initialized flag tracks whether initialization has occurred.
        
        Architecture (Clean Separation of Concerns):
            YAML File (configuration.yml)
                ↓
            ConfigManager (load + provide raw config)
                └─ get_adapter_mode_and_config() → raw config
                ↓
            SubmodelServiceManager (bridge - orchestrate + transform)
                ├─ Gets raw config from ConfigManager
                ├─ Uses AdapterConfigurationInterface to transform via factory pattern
                └─ Passes transformed config to SubmodelAdapterFactory.from_config()
                ↓
            SubmodelAdapterFactory (creates adapter from transformed config)
                └─ from_config() builds adapter instance
        
        Configuration Flow:
        1. ConfigManager.get_adapter_mode_and_config()
           → Returns: (adapter_mode, raw_config_from_yaml)
        
        2. AdapterConfigurationInterface.transform_config()
           → Transforms raw YAML config to adapter-specific format
           → path → root_path (FileSystem)
           → Flattens nested auth structures (HTTP Submodel, S3)
        
        3. SubmodelAdapterFactory.from_config()
           → Creates adapter using transformed config
        
        Note on Singleton Pattern:
        The singleton __new__() method is prepared but currently commented out. If enabled
        in the future, it will enforce that only one manager instance exists application-wide.
        The current lazy initialization pattern provides similar benefits for typical usage.
        
        Raises:
            ValueError: If configuration section is missing or invalid
            RuntimeError: If adapter initialization fails
        
        Example:
            # First instantiation initializes adapter from configuration
            manager = SubmodelServiceManager()
            
            # Subsequent instantiations skip initialization (lazy pattern)
            manager2 = SubmodelServiceManager()
            # Both have access to the initialized adapter
        """
        if SubmodelServiceManager._initialized:
            return
        
        try:
            # Step 1: Get raw adapter mode and config from ConfigManager
            # ConfigManager is purely a config provider (no transformations)
            self.adapter_mode, raw_adapter_config = ConfigManager.get_adapter_mode_and_config(
                validate_adapter_exists=True
            )
            
            # Step 2: Transform raw config using SubmodelAdapterFactory interface
            # AdapterConfigurationInterface handles adapter-specific transformations
            transformed_adapter_config = AdapterConfigurationInterface.transform_config(
                self.adapter_mode,
                raw_adapter_config
            )
            
            # Step 3: Pass transformed config to factory to create adapter
            # SubmodelAdapterFactory.from_config() builds the adapter instance
            self.adapter = SubmodelAdapterFactory.from_config(
                self.adapter_mode,
                transformed_adapter_config
            )
            
            SubmodelServiceManager._initialized = True
            self.logger.info(
                f"SubmodelServiceManager initialized successfully with adapter mode: {self.adapter_mode}"
            )
        except ValueError as e:
            self.logger.error(f"Configuration error during initialization: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize SubmodelServiceManager: {e}")
            raise RuntimeError(f"Failed to initialize submodel adapter: {e}") from e

    @classmethod
    def register_external_adapter(
        cls,
        adapter_type: str,
        builder_factory: Callable | None = None,
        adapter_class: Any = None,
        overwrite: bool = False,
    ) -> None:
        """
        Register an external (custom) adapter type at runtime.

        Allows dynamic registration of adapter implementations that are not built-in
        to the SDK. Provide either a builder factory or an adapter class with a
        ``builder()`` classmethod.

        Args:
            adapter_type: External adapter type key (e.g., "custom_adapter").
            builder_factory: Callable that returns a configured builder instance.
                Mutually exclusive with ``adapter_class``.
            adapter_class: Adapter class exposing a ``builder()`` classmethod.
                Mutually exclusive with ``builder_factory``.
            overwrite: If True, overwrites existing registration with the same type.
                Default: False (raises ValueError if already registered).

        Raises:
            ValueError: If neither builder_factory nor adapter_class is provided,
                or if type already exists and overwrite=False.
            TypeError: If builder_factory is not callable or adapter_class
                lacks a callable ``builder()`` method.

        Example:
            Register a custom adapter class::

                class MyCustomAdapter:
                    @classmethod
                    def builder(cls):
                        return cls._Builder()

                SubmodelServiceManager.register_external_adapter(
                    adapter_type="my_custom",
                    adapter_class=MyCustomAdapter,
                )
        """
        # Validate that at least one parameter is provided
        if builder_factory is None and adapter_class is None:
            raise ValueError(
                "Either 'builder_factory' or 'adapter_class' must be provided. "
                "Both cannot be None."
            )

        # Validate builder_factory if provided
        if builder_factory is not None and not callable(builder_factory):
            raise TypeError(
                f"'builder_factory' must be callable, got {type(builder_factory).__name__}"
            )

        # Validate adapter_class if provided
        if adapter_class is not None:
            if not hasattr(adapter_class, "builder"):
                raise TypeError(
                    f"'adapter_class' must have a 'builder' classmethod. "
                    f"Class {adapter_class.__name__} does not have one."
                )
            if not callable(getattr(adapter_class, "builder")):
                raise TypeError(
                    f"'adapter_class.builder' must be callable. "
                    f"Got {type(getattr(adapter_class, 'builder')).__name__}"
                )

        # Check for duplicate registration
        if adapter_type in cls._external_adapters and not overwrite:
            raise ValueError(
                f"Adapter type '{adapter_type}' is already registered. "
                f"Set overwrite=True to replace the existing registration."
            )

        try:
            SubmodelAdapterFactory.register_adapter(
                adapter_type=adapter_type,
                builder_factory=builder_factory,
                adapter_class=adapter_class,
                overwrite=overwrite,
            )
            # Track in our own registry
            cls._external_adapters[adapter_type] = {
                "builder_factory": builder_factory,
                "adapter_class": adapter_class,
            }
            cls.logger.info(
                f"External adapter '{adapter_type}' registered successfully. "
                f"Available external adapters: {cls.get_registered_adapters()}"
            )
        except (ValueError, TypeError) as e:
            cls.logger.error(f"Failed to register external adapter '{adapter_type}': {e}")
            raise

    @classmethod
    def get_registered_adapters(cls) -> list[str]:
        """
        Get list of externally registered (custom) adapter types.

        This method returns only adapters registered at runtime via
        ``register_external_adapter()``. Built-in adapters (FileSystem, S3,
        HttpSubmodel) are intentionally excluded.

        Returns:
            Sorted list of registered external adapter type keys.

        Example:
            Inspect runtime registrations::

                external = SubmodelServiceManager.get_registered_adapters()
                # Returns: ['my_custom', 'another_adapter']
        """
        # Return from our own registry (most reliable)
        adapters = sorted(list(cls._external_adapters.keys()))
        cls.logger.debug(f"Registered external adapter types: {adapters}")
        return adapters

    @classmethod
    def unregister_external_adapter(cls, adapter_type: str) -> None:
        """
        Unregister a previously registered external adapter type.

        Removes a custom adapter from the runtime registry. Built-in adapters
        cannot be unregistered.

        Args:
            adapter_type: External adapter type key to unregister.

        Raises:
            ValueError: If adapter_type is not registered or is a built-in adapter.

        Example:
            Remove a custom adapter::

                SubmodelServiceManager.unregister_external_adapter("my_custom")
        """
        # Check if adapter is registered (in our registry)
        if adapter_type not in cls._external_adapters:
            raise ValueError(
                f"Adapter type '{adapter_type}' is not registered or does not exist. "
                f"Cannot unregister a non-existent adapter. "
                f"Available registered adapters: {cls.get_registered_adapters()}"
            )

        try:
            SubmodelAdapterFactory.unregister_adapter(adapter_type=adapter_type)
            # Remove from our registry
            del cls._external_adapters[adapter_type]
            cls.logger.info(
                f"External adapter '{adapter_type}' unregistered successfully. "
                f"Remaining registered adapters: {cls.get_registered_adapters()}"
            )
        except Exception as e:
            cls.logger.error(f"Failed to unregister external adapter '{adapter_type}': {e}")
            raise

    def _validate_uuid(self, value: Any) -> UUID:
        """Validate and convert value to UUID.
        
        Args:
            value: Value to validate as UUID.
        
        Returns:
            Valid UUID instance.
        
        Raises:
            InvalidError: If value cannot be converted to UUID.
        """
        if isinstance(value, UUID):
            return value
        try:
            return UUID(value)
        except (ValueError, AttributeError, TypeError) as e:
            raise InvalidError(f"Invalid UUID: {value}") from e

    def _hash_semantic_id(self, semantic_id: str) -> str:
        """Generate SHA-256 hash of semantic ID for storage organization.
        
        Creates a deterministic hash of the semantic ID that can be used for organizing
        storage paths or grouping related submodels.
        
        Args:
            semantic_id: Semantic ID of the submodel (e.g., urn:samm:io.catenax...).
        
        Returns:
            SHA-256 hash of the semantic ID as hexadecimal string.
        """
        sha256_semantic_id = sha256(semantic_id.encode()).hexdigest()
        return sha256_semantic_id
    
    def _execute_submodel_operation(
        self,
        operation: OperationType,
        submodel_id: UUID,
        semantic_id: str,
        payload: Dict[str, Any] | None = None
    ) -> Dict[str, Any] | None:
        """Execute a submodel operation (read, write, delete) in a generalized manner.
        
        This method handles the branching logic between HTTP and filesystem adapters,
        reducing code duplication across read/write/delete operations.
        
        Args:
            operation: Type of operation to perform.
            submodel_id: UUID of the submodel.
            semantic_id: Semantic ID of the submodel.
            payload: Payload data for write operations.
        
        Returns:
            Operation result (content for read operations, None for write/delete).
        
        Raises:
            InvalidError: If submodel_id is invalid.
            NotFoundError: If submodel not found during read/delete.
        """
        submodel_id = self._validate_uuid(submodel_id)
        
        # Log operation
        self.logger.info(f"{operation.value.capitalize()}ing submodel with id=[{submodel_id}], semanticId=[{semantic_id}]")
        
        # Create metadata object for adapter communication
        submodel_metadata = SubmodelMetadata(
            submodel_id=str(submodel_id),
            semantic_id=semantic_id,
            semantic_id_hash=self._hash_semantic_id(semantic_id),
        )
        
        if operation == OperationType.READ:
            if not self.adapter.exists(submodel_metadata.to_dict()):
                self.logger.error(f"Submodel file not found: {submodel_metadata}")
                raise NotFoundError(f"Submodel file not found: {submodel_metadata}")
            return self.adapter.read(submodel_metadata.to_dict())
        
        elif operation == OperationType.WRITE:
            self.logger.info(f"Writing submodel with metadata: {submodel_metadata.to_dict()}")
            self.adapter.write_json(submodel_metadata.to_dict(), payload)
            self.logger.info("Submodel uploaded successfully.")
            return None
        
        elif operation == OperationType.DELETE:
            if not self.adapter.exists(submodel_metadata.to_dict()):
                self.logger.error(f"Submodel file not found: {submodel_metadata}")
                raise NotFoundError(f"Submodel file not found: {submodel_metadata}")
            self.adapter.delete(submodel_metadata.to_dict())
            self.logger.info("Submodel deleted successfully.")
            return None

    def upload_twin_aspect_document(
        self,
        submodel_id: UUID,
        semantic_id: str,
        payload: Dict[str, Any]
    ) -> None:
        """
        Upload a submodel to the configured storage backend.
        
        Uploads a JSON-serializable submodel document to the underlying storage
        system (FileSystem, S3, or external HTTP submodel service) based on the
        configured adapter.
        
        Args:
            submodel_id: UUID of the submodel being uploaded.
            semantic_id: Semantic ID (e.g., urn:example:submodel) that identifies
                the submodel type. Used for storage path organization.
            payload: Submodel content as a dictionary. Must be JSON-serializable.
        
        Returns:
            None
        
        Raises:
            InvalidError: If submodel_id is not a valid UUID.
            RuntimeError: If adapter is not initialized or storage operation fails.
        
        Example:
            payload = {
                "modelType": "Submodel",
                "identification": "...",
                "submodelElements": [...]
            }
            manager.upload_twin_aspect_document(
                submodel_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
                semantic_id="urn:example:submodel:v1",
                payload=payload
            )
        """
        self._execute_submodel_operation(
            OperationType.WRITE,
            submodel_id,
            semantic_id,
            payload
        )

    def get_twin_aspect_document(
        self,
        submodel_id: UUID,
        semantic_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve a submodel from the configured storage backend.
        
        Fetches a previously uploaded submodel document from the underlying storage
        system (FileSystem, S3, or external HTTP submodel service) by its UUID and
        semantic ID.
        
        Args:
            submodel_id: UUID of the submodel to retrieve.
            semantic_id: Semantic ID used to locate the submodel in storage.
        
        Returns:
            Submodel content as a dictionary with full AAS structure
            (modelType, identification, submodelElements, etc.).
        
        Raises:
            InvalidError: If submodel_id is not a valid UUID.
            NotFoundError: If the submodel does not exist in storage.
            RuntimeError: If adapter is not initialized or retrieval fails.
        
        Example:
            submodel = manager.get_twin_aspect_document(
                submodel_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
                semantic_id="urn:example:submodel:v1"
            )
            print(f"Submodel type: {submodel['modelType']}")
        """
        return self._execute_submodel_operation(
            OperationType.READ,
            submodel_id,
            semantic_id
        )

    def delete_twin_aspect_document(
        self,
        submodel_id: UUID,
        semantic_id: str
    ) -> None:
        """
        Delete a submodel from the configured storage backend.
        
        Removes a submodel document from the underlying storage system (FileSystem,
        S3, or external HTTP submodel service). The submodel must exist; attempting
        to delete a non-existent submodel raises NotFoundError.
        
        Args:
            submodel_id: UUID of the submodel to delete.
            semantic_id: Semantic ID used to locate the submodel in storage.
        
        Returns:
            None
        
        Raises:
            InvalidError: If submodel_id is not a valid UUID.
            NotFoundError: If the submodel does not exist in storage.
            RuntimeError: If adapter is not initialized or deletion fails.
        
        Example:
            manager.delete_twin_aspect_document(
                submodel_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
                semantic_id="urn:example:submodel:v1"
            )
            print("Submodel deleted successfully")
        """
        self._execute_submodel_operation(
            OperationType.DELETE,
            submodel_id,
            semantic_id
        )
