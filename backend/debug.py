import os

class Debug:
    def find_server_file(self, project_path):
        """Find the main server file for the MCP server."""
        # Common server file names
        possible_files = ['server.py', 'main.py', 'app.py', '__main__.py']
        
        # Search directories in order of preference
        search_dirs = [
            '',  # root directory
            'src/',  # common Python package structure
            'src/playwright_server/',  # specific playwright project structure
            'server/',  # server subdirectory
        ]
        
        for search_dir in search_dirs:
            search_path = os.path.join(project_path, search_dir)
            if os.path.exists(search_path):
                self.log(f"Searching in directory: {search_path}")
                for filename in possible_files:
                    filepath = os.path.join(search_path, filename)
                    if os.path.exists(filepath):
                        self.log(f"Found server file: {filepath}")
                        return filepath
        
        # List what we actually found for debugging
        self.log(f"No server file found. Searched in:")
        for search_dir in search_dirs:
            search_path = os.path.join(project_path, search_dir)
            if os.path.exists(search_path):
                try:
                    files = os.listdir(search_path)
                    self.log(f"  {search_path}: {files}")
                except Exception as e:
                    self.log(f"  {search_path}: Error listing - {e}")
            else:
                self.log(f"  {search_path}: Directory does not exist")
        
        return None 