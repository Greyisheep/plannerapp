import logging
import os
from typing import Annotated

from semantic_kernel.functions.kernel_function_decorator import kernel_function

logger = logging.getLogger(__name__)

class FileIOPlugin:
    """Plugin for performing file input/output operations."""

    def __init__(self, base_directory: str | None = None):
        """Initializes the FileIOPlugin.

        Args:
            base_directory: The base directory for file operations. 
                            Defaults to the current working directory.
        """
        self._base_directory = base_directory or os.getcwd()
        # Ensure base directory exists, create if not (optional, consider security implications)
        # if not os.path.exists(self._base_directory):
        #     os.makedirs(self._base_directory)
        #     logger.info(f"Created base directory: {self._base_directory}")
        logger.info(f"FileIOPlugin initialized with base directory: {self._base_directory}")

    def _get_safe_path(self, file_name: str) -> str | None:
        """Constructs a safe file path and ensures it's within the base directory."""
        # Sanitize file_name to prevent directory traversal (e.g., remove '..')
        safe_file_name = os.path.basename(file_name)
        if safe_file_name != file_name:
            logger.warning(f"Potentially unsafe file name '{file_name}' sanitized to '{safe_file_name}'.")
        
        full_path = os.path.join(self._base_directory, safe_file_name)
        
        # Final check to ensure the path is within the intended directory
        if os.path.commonprefix([os.path.realpath(full_path), os.path.realpath(self._base_directory)]) != os.path.realpath(self._base_directory):
            logger.error(f"Attempt to access path '{full_path}' outside of base directory '{self._base_directory}'. Denying operation.")
            return None
        return full_path

    @kernel_function(
        description="Writes content to a file, overwriting if it exists.",
        name="write_to_file"
    )
    def write_to_file(
        self, 
        file_name: Annotated[str, "The name of the file to write to (e.g., 'output.txt')."],
        content: Annotated[str, "The content to write to the file."]
    ) -> Annotated[str, "A message indicating success or failure."]:
        logger.info(f"Attempting to write to file: {file_name}")
        safe_path = self._get_safe_path(file_name)
        if not safe_path:
            return "Failed to write to file: Invalid file path or access denied."
        try:
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Content written to '{safe_path}'.")
            return f"Content written to '{file_name}'."
        except Exception as e:
            logger.error(f"Failed to write to file '{safe_path}': {e}")
            return f"Failed to write to file '{file_name}': {e}"

    @kernel_function(
        description="Appends content to a file.",
        name="append_to_file"
    )
    def append_to_file(
        self, 
        file_name: Annotated[str, "The name of the file to append to (e.g., 'log.txt')."],
        content: Annotated[str, "The content to append."]
    ) -> Annotated[str, "A message indicating success or failure."]:
        logger.info(f"Attempting to append to file: {file_name}")
        safe_path = self._get_safe_path(file_name)
        if not safe_path:
            return "Failed to append to file: Invalid file path or access denied."
        try:
            with open(safe_path, "a", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Content appended to '{safe_path}'.")
            return f"Content appended to '{file_name}'."
        except Exception as e:
            logger.error(f"Failed to append to file '{safe_path}': {e}")
            return f"Failed to append to file '{file_name}': {e}"

    @kernel_function(
        description="Reads the content of a file.",
        name="read_file_content"
    )
    def read_file(
        self, 
        file_name: Annotated[str, "The name of the file to read (e.g., 'input.txt')."]
    ) -> Annotated[str, "The content of the file, or an error message."]:
        logger.info(f"Attempting to read file: {file_name}")
        safe_path = self._get_safe_path(file_name)
        if not safe_path:
            return "Failed to read file: Invalid file path or access denied."
        try:
            if not os.path.exists(safe_path):
                logger.warning(f"File '{safe_path}' does not exist for reading.")
                return f"File '{file_name}' does not exist."
            with open(safe_path, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info(f"Content read from '{safe_path}'.")
            return content
        except Exception as e:
            logger.error(f"Failed to read file '{safe_path}': {e}")
            return f"Failed to read file '{file_name}': {e}"

    @kernel_function(
        description="Deletes a file.",
        name="delete_file_by_name"
    )
    def delete_file(
        self, 
        file_name: Annotated[str, "The name of the file to delete (e.g., 'temp.txt')."]
    ) -> Annotated[str, "A message indicating success or failure."]:
        logger.info(f"Attempting to delete file: {file_name}")
        safe_path = self._get_safe_path(file_name)
        if not safe_path:
            return "Failed to delete file: Invalid file path or access denied."
        try:
            if not os.path.exists(safe_path):
                logger.warning(f"File '{safe_path}' does not exist for deletion.")
                return f"File '{file_name}' does not exist."
            os.remove(safe_path)
            logger.info(f"File '{safe_path}' deleted.")
            return f"File '{file_name}' deleted."
        except Exception as e:
            logger.error(f"Failed to delete file '{safe_path}': {e}")
            return f"Failed to delete file '{file_name}': {e}"

# Example usage (for testing the plugin directly):
if __name__ == "__main__":
    # Create a dummy directory for testing relative paths
    test_dir = "_file_io_test_dir"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)

    # Test with a base directory
    print(f"--- Testing with base directory: {test_dir} ---")
    plugin = FileIOPlugin(base_directory=test_dir)
    
    test_file = "test_file.txt"
    print(plugin.write_to_file(test_file, "Hello from FileIOPlugin!\n"))
    print(plugin.read_file(test_file))
    print(plugin.append_to_file(test_file, "Appending some more text.\n"))
    print(plugin.read_file(test_file))
    # Test reading non-existent file
    print(plugin.read_file("non_existent_file.txt"))
    # Test deleting file
    print(plugin.delete_file(test_file))
    print(plugin.read_file(test_file)) # Should say it doesn't exist
    # Test deleting non-existent file
    print(plugin.delete_file("non_existent_file.txt"))

    # Test unsafe paths
    print("--- Testing unsafe paths ---")
    print(plugin.write_to_file("../unsafe_test.txt", "This should not write outside."))
    print(plugin.read_file("../../../../../../../../../../../../etc/hosts")) # Example of trying to read sensitive file

    # Clean up the dummy directory
    if os.path.exists(os.path.join(test_dir, "../unsafe_test.txt")):
        os.remove(os.path.join(test_dir, "../unsafe_test.txt"))
        print("Cleaned up unsafe_test.txt (this indicates a security flaw if it was created)")
    
    if os.path.exists(test_dir):
        for f in os.listdir(test_dir):
            os.remove(os.path.join(test_dir, f))
        os.rmdir(test_dir)
        print(f"Cleaned up test directory: {test_dir}")

    # Test without a base directory (uses current working directory)
    print("\n--- Testing with default base directory (current working directory) ---")
    plugin_no_base = FileIOPlugin()
    test_file_cwd = "test_file_cwd.txt"
    print(plugin_no_base.write_to_file(test_file_cwd, "Hello in CWD!\n"))
    print(plugin_no_base.read_file(test_file_cwd))
    print(plugin_no_base.delete_file(test_file_cwd))
    print(f"Cleaned up {test_file_cwd}") 