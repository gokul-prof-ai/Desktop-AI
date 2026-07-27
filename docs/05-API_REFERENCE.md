# API Reference

## Module: Scanner

\`\`\`python
class FileScanner:
def scan(
folder: str,
max_depth: int = 5,
ignore_patterns: List[str] = None
) -> List[FileInfo]:
"""
Recursively scan folder for files.

        Args:
            folder: Path to scan
            max_depth: Maximum directory depth (default: 5)
            ignore_patterns: Patterns to ignore (e.g., ['.git', '__pycache__'])

        Returns:
            List of FileInfo objects with metadata

        Raises:
            PermissionError: If no read access
            OSError: If path doesn't exist

        Examples:
            >>> scanner = FileScanner()
            >>> files = scanner.scan('/home/user/docs')
            >>> print(f"Found {len(files)} files")
        """

\`\`\`

## Module: Organizer

[Similarly detailed]

## Module: Search

[Similarly detailed]
