import logging
import os

logger = logging.getLogger(__name__)

class FileIOTool:
    """Tool for performing file input/output operations."""

    def __init__(self, base_directory: str | None = None):
        """Initializes the FileIOTool.

        Args:
            base_directory: The base directory for file operations. 
                            Defaults to a subdirectory named 'adk_tool_files' 
                            within the current working directory of the ADK agent.
        """
        # If base_directory is not specified, default to a specific subdir for ADK tools
        if base_directory is None:
            self._base_directory = os.path.join(os.getcwd(), "adk_tool_files")
        else:
            self._base_directory = base_directory
        
        if not os.path.exists(self._base_directory):
            try:
                os.makedirs(self._base_directory)
                logger.info(f"Created base directory for FileIOTool: {self._base_directory}")
            except OSError as e:
                logger.error(f"Failed to create base directory {self._base_directory}: {e}")
                # Depending on desired behavior, you might want to raise an error here
                # or ensure all file operations will fail gracefully.
                # For now, we log and proceed, operations will likely fail if dir doesn't exist.

        logger.info(f"FileIOTool initialized with base directory: {self._base_directory}")

    def _get_safe_path(self, file_name: str) -> str | None:
        """Constructs a safe file path and ensures it's within the base directory."""
        if not self._base_directory or not os.path.exists(self._base_directory):
            logger.error(f"Base directory '{self._base_directory}' does not exist or is not set. Cannot perform file operations.")
            return None

        # Sanitize file_name to prevent directory traversal (e.g., remove '..')
        safe_file_name = os.path.basename(file_name)
        if safe_file_name != file_name:
            logger.warning(f"Potentially unsafe file name '{file_name}' sanitized to '{safe_file_name}'.")
        
        full_path = os.path.join(self._base_directory, safe_file_name)
        
        # Final check to ensure the path is within the intended directory
        # os.path.realpath resolves symlinks, which is good for security.
        if os.path.commonprefix([os.path.realpath(full_path), os.path.realpath(self._base_directory)]) != os.path.realpath(self._base_directory):
            logger.error(f"Attempt to access path '{full_path}' outside of base directory '{self._base_directory}'. Denying operation.")
            return None
        return full_path

    def write_to_file(
        self, 
        file_name: str,
        content: str
    ) -> str:
        """Writes content to a file, overwriting if it exists."""
        logger.info(f"Attempting to write to file: {file_name}")
        safe_path = self._get_safe_path(file_name)
        if not safe_path:
            return "Failed to write to file: Invalid file path, access denied, or base directory issue."
        try:
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Content written to '{safe_path}'.")
            return f"Content written to '{file_name}' in directory '{os.path.basename(self._base_directory)}'."
        except Exception as e:
            logger.error(f"Failed to write to file '{safe_path}': {e}")
            return f"Failed to write to file '{file_name}': {e}"

    def append_to_file(
        self, 
        file_name: str,
        content: str
    ) -> str:
        """Appends content to a file."""
        logger.info(f"Attempting to append to file: {file_name}")
        safe_path = self._get_safe_path(file_name)
        if not safe_path:
            return "Failed to append to file: Invalid file path, access denied, or base directory issue."
        try:
            with open(safe_path, "a", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Content appended to '{safe_path}'.")
            return f"Content appended to '{file_name}' in directory '{os.path.basename(self._base_directory)}'."
        except Exception as e:
            logger.error(f"Failed to append to file '{safe_path}': {e}")
            return f"Failed to append to file '{file_name}': {e}"

    def read_file_content(
        self, 
        file_name: str
    ) -> str:
        """Reads the content of a file."""
        logger.info(f"Attempting to read file: {file_name}")
        safe_path = self._get_safe_path(file_name)
        if not safe_path:
            return "Failed to read file: Invalid file path, access denied, or base directory issue."
        try:
            if not os.path.exists(safe_path):
                logger.warning(f"File '{safe_path}' does not exist for reading.")
                return f"File '{file_name}' does not exist in directory '{os.path.basename(self._base_directory)}'."
            with open(safe_path, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info(f"Content read from '{safe_path}'.")
            return content
        except Exception as e:
            logger.error(f"Failed to read file '{safe_path}': {e}")
            return f"Failed to read file '{file_name}': {e}"

    def delete_file_by_name(
        self, 
        file_name: str
    ) -> str:
        """Deletes a file."""
        logger.info(f"Attempting to delete file: {file_name}")
        safe_path = self._get_safe_path(file_name)
        if not safe_path:
            return "Failed to delete file: Invalid file path, access denied, or base directory issue."
        try:
            if not os.path.exists(safe_path):
                logger.warning(f"File '{safe_path}' does not exist for deletion.")
                return f"File '{file_name}' does not exist in directory '{os.path.basename(self._base_directory)}'."
            os.remove(safe_path)
            logger.info(f"File '{safe_path}' deleted.")
            return f"File '{file_name}' deleted from directory '{os.path.basename(self._base_directory)}'."
        except Exception as e:
            logger.error(f"Failed to delete file '{safe_path}': {e}")
            return f"Failed to delete file '{file_name}': {e}"

# Example usage (for testing the tool directly):
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Test with a specific base directory relative to this script file
    # This makes the test self-contained within the @ADK folder if run directly.
    script_dir = os.path.dirname(__file__) # Gets directory of adk_file_io_tool.py
    test_dir = os.path.join(script_dir, "_adk_file_io_test_dir")
    print(f"--- Testing with base directory: {test_dir} ---")
    
    tool = FileIOTool(base_directory=test_dir)
    
    test_file = "my_test_file.txt"
    print(tool.write_to_file(test_file, "Hello from ADK FileIOTool!\n"))
    print(f"Read content: {tool.read_file_content(test_file)}")
    print(tool.append_to_file(test_file, "Appending some more text to the ADK file.\n"))
    print(f"Read content after append: {tool.read_file_content(test_file)}")
    
    # Test reading non-existent file
    print(tool.read_file_content("ghost_file.txt"))
    
    # Test deleting file
    print(tool.delete_file_by_name(test_file))
    print(tool.read_file_content(test_file)) # Should say it doesn't exist
    
    # Test deleting non-existent file
    print(tool.delete_file_by_name("ghost_file.txt"))

    # Test unsafe paths
    print("--- Testing unsafe paths (should be denied) ---")
    # Attempt to write outside the designated test_dir. 
    # os.path.basename will sanitize this, but _get_safe_path provides the real check.
    print(tool.write_to_file("../unsafe_adk_test.txt", "This should not write outside ADK tool's base dir."))
    # The FileIOTool is initialized with test_dir. Attempting to access /etc/hosts (or C:\Windows\System32\drivers\etc\hosts on Win)
    # should be blocked because realpath of that won't be prefixed by realpath of test_dir.
    sensitive_file_attempt = "../../../../../../../../../../../../etc/hosts" # A deeply nested attempt
    if os.name == 'nt':
        sensitive_file_attempt = "../../../../../../../../../../../../Windows/System32/drivers/etc/hosts"
    print(tool.read_file_content(sensitive_file_attempt)) 

    # Clean up the dummy directory and any accidentally created unsafe files
    if os.path.exists(os.path.join(test_dir, "../unsafe_adk_test.txt")):
        # This check is mostly for an OS where os.path.basename might not prevent ../ on its own
        # and if _get_safe_path somehow failed (it shouldn't).
        try:
            os.remove(os.path.join(test_dir, "../unsafe_adk_test.txt"))
            print("Cleaned up unsafe_adk_test.txt (this indicates a security flaw if it was created outside test_dir)")
        except OSError as e:
            print(f"Could not remove unsafe_adk_test.txt: {e}")

    if os.path.exists(test_dir):
        for f_name in os.listdir(test_dir):
            try:
                os.remove(os.path.join(test_dir, f_name))
            except OSError as e_remove:
                print(f"Could not remove {f_name} from {test_dir}: {e_remove}")
        try:
            os.rmdir(test_dir)
            print(f"Cleaned up ADK test directory: {test_dir}")
        except OSError as e_rmdir:
            print(f"Could not remove directory {test_dir}: {e_rmdir}")

    print("\n--- Testing with default base directory (adk_tool_files in CWD) ---")
    default_tool_base_dir = os.path.join(os.getcwd(), "adk_tool_files")
    tool_default_base = FileIOTool() # Uses default base_directory
    test_file_cwd = "test_file_in_default_adk_dir.txt"
    print(tool_default_base.write_to_file(test_file_cwd, "Hello in ADK default CWD tool files!\n"))
    print(f"Read from default base: {tool_default_base.read_file_content(test_file_cwd)}")
    print(tool_default_base.delete_file_by_name(test_file_cwd))
    print(f"Cleaned up {test_file_cwd} from {tool_default_base._base_directory}")
    # Clean up the default adk_tool_files directory if it's empty and was created by this test
    if os.path.exists(default_tool_base_dir) and not os.listdir(default_tool_base_dir):
        try:
            os.rmdir(default_tool_base_dir)
            print(f"Cleaned up default base directory: {default_tool_base_dir}")
        except OSError as e_rmdir_default:
            print(f"Could not remove default base directory {default_tool_base_dir}: {e_rmdir_default}") 