from typing import Dict, Any
from managers.config.log_manager import LoggingManager


class AdapterConfigurationInterface:
    """
    Interface for SubmodelAdapterFactory configuration transformations.

    Provides static methods that wrap SubmodelAdapterFactory's transformation
    capabilities, allowing clean delegation of adapter-specific config transformations.
    This interface abstracts the transformation logic away from SubmodelServiceManager.

    The interface methods follow the pattern:
        raw_config (from YAML) → transform_config() → transformed_config (for adapter)
    """

    @staticmethod
    def transform_config(
        adapter_type: str, raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform adapter configuration from YAML format to factory-expected format.

        Delegates to adapter-type-specific transformation methods via SubmodelAdapterFactory interface.

        Args:
            adapter_type: Normalized adapter type (lowercase with underscores)
            raw_config: Raw configuration dictionary from YAML

        Returns:
            Transformed configuration dictionary ready for SubmodelAdapterFactory

        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(raw_config, dict):
            raise ValueError(
                f"Configuration must be a dictionary, got {type(raw_config).__name__}"
            )

        # Create a copy to avoid modifying the original
        config = raw_config.copy()

        if adapter_type == "file_system":
            return AdapterConfigurationInterface.transform_file_system_config(config)
        elif adapter_type == "http_submodel":
            return AdapterConfigurationInterface.transform_http_submodel_config(config)
        elif adapter_type == "s3":
            return AdapterConfigurationInterface.transform_s3_config(config)

        return config

    @staticmethod
    def transform_file_system_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform FileSystem adapter configuration via SubmodelAdapterFactory interface.

        Converts YAML-formatted config to factory-expected format:
            path: "..." → root_path: "..."
        """
        if "path" in config:
            config["root_path"] = config.pop("path")
            LoggingManager.get_logger(__name__).debug(
                "Transformed 'path' field to 'root_path' for FileSystem adapter"
            )
        return config

    @staticmethod
    def transform_http_submodel_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform HTTP Submodel adapter configuration via SubmodelAdapterFactory interface.

        Flattens nested auth structure to factory-expected format:
            auth:
              token: "..." → auth_token: "..."
              key_name: "..." → auth_key_name: "..."
        """
        if "auth" in config:
            auth_config = config.pop("auth")
            if isinstance(auth_config, dict):
                if "token" in auth_config:
                    config["auth_token"] = auth_config["token"]
                if "key_name" in auth_config:
                    config["auth_key_name"] = auth_config["key_name"]
                LoggingManager.get_logger(__name__).debug(
                    "Flattened 'auth' structure to 'auth_token' and 'auth_key_name' for HTTP Submodel adapter"
                )
        return config

    @staticmethod
    def transform_s3_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform S3 adapter configuration via SubmodelAdapterFactory interface.

        Flattens nested auth structure to factory-expected format:
            auth:
              aws_access_key_id: "..." → aws_access_key_id: "..."
              aws_secret_access_key: "..." → aws_secret_access_key: "..."
        """
        if "auth" in config:
            auth_config = config.pop("auth")
            if isinstance(auth_config, dict):
                if "aws_access_key_id" in auth_config:
                    config["aws_access_key_id"] = auth_config["aws_access_key_id"]
                if "aws_secret_access_key" in auth_config:
                    config["aws_secret_access_key"] = auth_config[
                        "aws_secret_access_key"
                    ]
                LoggingManager.get_logger(__name__).debug(
                    "Flattened 'auth' structure to 'aws_access_key_id' and 'aws_secret_access_key' for S3 adapter"
                )
        return config
