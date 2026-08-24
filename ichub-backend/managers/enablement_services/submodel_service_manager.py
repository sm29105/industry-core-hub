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

import json
from dataclasses import dataclass
from typing import Dict, Any, Callable
from uuid import UUID
from hashlib import sha256
from enum import Enum

from managers.config.log_manager import LoggingManager
from managers.config.config_manager import ConfigManager
from tools.exceptions import InvalidError, NotFoundError

from tractusx_sdk.industry.adapters.submodel_adapter_factory import SubmodelAdapterFactory
from managers.enablement_services.adapters.adapter_config_manager import SubmodelAdapterProvider


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
    
    Creates one adapter per manager instance from the configured dispatcher section.
    Adapter initialization is dynamic and delegated to SubmodelAdapterFactory.
    Supports multiple storage backends:
    - FileSystem (local storage)
    - S3 (AWS S3 or S3-compatible)
    - HttpSubmodel (external submodel service)
    
    Configuration is loaded from YAML and passed to the factory without any hardcoded logic
    or switch statements. Adapter type and configuration are determined dynamically from
    the configuration section: provider.submodel_dispatcher
    
    Example:
        # Initialize adapter from configuration
        manager = SubmodelServiceManager()
        
        # A manager built from the same dispatcher section reuses the cached adapter.
        manager2 = SubmodelServiceManager()
        # A manager pointed at a different dispatcher section builds/caches its own adapter.
        manager3 = SubmodelServiceManager("provider.secondary_dispatcher")
    """
    logger = LoggingManager.get_logger(__name__)

    # Adapter instances are cached per resolved source so repeated instantiations
    # (e.g. one per request) reuse the same adapter instead of rebuilding it.
    # Cache structure: {cache_key: {"adapter": adapter_instance, "mode": adapter_type_string}}
    _adapter_cache: Dict[str, Dict[str, Any]] = {}

    def __init__(
        self,
        dispatcher_path: str = "provider.submodel_dispatcher",
        adapter_type: str | None = None,
        adapter_config: Dict[str, Any] | None = None,
    ):
        """
        Initialize a manager with an adapter selected from the given configuration section.
        
        Architecture (Clean Separation of Concerns):
            YAML File (configuration.yml)
                ↓
            ConfigManager (load + provide raw config)
                └─ get_adapter_mode_and_config() → raw config
                ↓
            SubmodelServiceManager (bridge - orchestrate)
                └─ SubmodelAdapterProvider loads and builds the configured adapter
                    ↓
                SubmodelAdapterFactory (creates adapter from builder-compatible config)
                    └─ from_config() builds adapter instance
        
        Configuration Flow:
          Adapter creation is delegated to SubmodelAdapterProvider so this manager
          does not depend on the YAML schema or adapter-specific mappings.
        
        Raises:
            ValueError: If configuration section is missing or invalid
            RuntimeError: If adapter initialization fails
        
        Example:
            # First instantiation builds and caches the adapter
            manager = SubmodelServiceManager()
            
            # Reuses the cached adapter, keyed by dispatcher_path
            manager2 = SubmodelServiceManager()
            
            # Different dispatcher path builds/caches a separate adapter
            manager3 = SubmodelServiceManager("provider.secondary_dispatcher")
        """
        try:
            adapter, adapter_mode = self._resolve_adapter(dispatcher_path, adapter_type, adapter_config)
            self.adapter = adapter
            self.adapter_mode = adapter_mode
        except ValueError as e:
            self.logger.error(f"Configuration error during initialization: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize SubmodelServiceManager: {e}")
            raise RuntimeError(f"Failed to initialize submodel adapter: {e}") from e

    def _resolve_adapter(
        self,
        dispatcher_path: str,
        adapter_type: str | None,
        adapter_config: Dict[str, Any] | None,
    ) -> tuple[Any, str]:
        """
        Resolve an adapter for the given source, reusing a cached instance if available.
        
        Returns:
            Tuple of (adapter_instance, adapter_mode_string)
        """
        if adapter_type is not None or adapter_config is not None:
            if adapter_type is None or adapter_config is None:
                raise ValueError(
                    "Both adapter_type and adapter_config are required for "
                    "frontend-configured adapters"
                )
            # Normalize so adapter_mode is consistent regardless of config source (YAML vs frontend/db).
            resolved_mode = adapter_type.strip().lower().replace(" ", "_").replace("-", "_")
            cache_key = self._build_cache_key(resolved_mode, adapter_config)
            source = f"frontend adapter '{resolved_mode}'"
        else:
            cache_key = f"dispatcher:{dispatcher_path}"
            source = f"dispatcher '{dispatcher_path}'"
            # Get the adapter mode from config
            resolved_mode, _ = ConfigManager.get_adapter_mode_and_config(
                dispatcher_path=dispatcher_path,
                validate_adapter_exists=True,
            )

        if cache_key in self._adapter_cache:
            self.logger.info(f"Reusing cached adapter for {source}")
            cached_data = self._adapter_cache[cache_key]
            return cached_data["adapter"], cached_data["mode"]

        # Provider resolves the source internally; manager stays source-agnostic.
        adapter = SubmodelAdapterProvider.create_adapter(
            dispatcher_path=dispatcher_path,
            adapter_type=adapter_type,
            adapter_config=adapter_config,
        )
        self._adapter_cache[cache_key] = {"adapter": adapter, "mode": resolved_mode}
        self.logger.info(f"SubmodelServiceManager initialized from {source}")
        return adapter, resolved_mode

    @staticmethod
    def _build_cache_key(adapter_type: str, adapter_config: Dict[str, Any]) -> str:
        """Build a stable cache key for a frontend-supplied adapter configuration."""
        try:
            config_signature = json.dumps(adapter_config, sort_keys=True, default=str)
        except TypeError:
            config_signature = repr(sorted(adapter_config.items(), key=str))
        config_hash = sha256(config_signature.encode("utf-8")).hexdigest()
        return f"frontend:{adapter_type}:{config_hash}"

    @classmethod
    def clear_adapter_cache(cls) -> None:
        """
        Clear all cached adapter instances.
        
        Use after reloading configuration or between test cases so the next
        manager instantiation rebuilds adapters from the current configuration.
        """
        cls._adapter_cache.clear()
        cls.logger.info("Submodel adapter cache cleared")

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
            ValueError: If exactly one of builder_factory or adapter_class is not provided,
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
        # Validate mutual exclusivity: exactly one registration path must be chosen.
        if (builder_factory is None) == (adapter_class is None):
            raise ValueError(
                "Exactly one of 'builder_factory' or 'adapter_class' must be provided. "
                "They are mutually exclusive."
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

        try:
            SubmodelAdapterFactory.register_adapter(
                adapter_type=adapter_type,
                builder_factory=builder_factory,
                adapter_class=adapter_class,
                overwrite=overwrite,
            )
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
        built_in_adapters = {"file_system", "http_submodel", "s3"}
        adapters = sorted(
            set(SubmodelAdapterFactory.get_available_adapter_types())
            - built_in_adapters
        )
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
        # Check if adapter is a built-in adapter
        built_in_adapters = {"file_system", "http_submodel", "s3"}
        if adapter_type in built_in_adapters:
            error_msg = f"Cannot unregister built-in adapter '{adapter_type}'. Built-in adapters are: {', '.join(sorted(built_in_adapters))}"
            cls.logger.error(error_msg)
            raise ValueError(error_msg)

        # Check if adapter is currently registered
        registered_adapters = cls.get_registered_adapters()
        if adapter_type not in registered_adapters:
            error_msg = f"Adapter '{adapter_type}' is not registered. Registered adapters are: {', '.join(sorted(registered_adapters)) if registered_adapters else 'none'}"
            cls.logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            SubmodelAdapterFactory.unregister_adapter(adapter_type=adapter_type)
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

        handlers = {
            OperationType.READ: self._read_submodel,
            OperationType.WRITE: self._write_submodel,
            OperationType.DELETE: self._delete_submodel,
        }
        return handlers[operation](submodel_metadata, payload)

    def _read_submodel(self, submodel_metadata: SubmodelMetadata, _payload: Dict[str, Any] | None) -> Dict[str, Any]:
        if not self.adapter.exists(submodel_metadata.to_dict()):
            self.logger.error(f"Submodel file not found: {submodel_metadata}")
            raise NotFoundError(f"Submodel file not found: {submodel_metadata}")
        return self.adapter.read(submodel_metadata.to_dict())

    def _write_submodel(self, submodel_metadata: SubmodelMetadata, payload: Dict[str, Any] | None) -> None:
        self.logger.info(f"Writing submodel with metadata: {submodel_metadata.to_dict()}")
        self.adapter.write_json(submodel_metadata.to_dict(), payload)
        self.logger.info("Submodel uploaded successfully.")
        return None

    def _delete_submodel(self, submodel_metadata: SubmodelMetadata, _payload: Dict[str, Any] | None) -> None:
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
