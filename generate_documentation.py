import os
from pathlib import Path
from datetime import datetime

# Directories and files to skip
SKIP_DIRS = {
    '__pycache__',
    '.git',
    'vosk-model-small-en-us-0.15',
    'vosk-model-small-hi-0.22',
    'venv',
    'env',
    '.venv',
    'node_modules',
    '.pytest_cache',
    '__pycache__'
}

SKIP_FILES = {
    '.pyc',
    '.pyo',
    '.pyd',
    '.so',
    '.dll',
    '.dylib',
    '.db',
    '.sqlite',
    '.log',
    'poetry.lock',
    '.DS_Store',
    'Thumbs.db'
}

IMPORTANT_EXTENSIONS = {
    '.py',
    '.toml',
    '.env.example',
    '.yml',
    '.yaml',
    '.json',
    '.md',
    '.txt',
    '.ini',
    '.cfg'
}

def should_skip_file(file_path):
    """Check if a file should be skipped."""
    file_name = os.path.basename(file_path)
    file_ext = os.path.splitext(file_name)[1]
    
    # Skip compiled Python files
    if file_ext in SKIP_FILES:
        return True
    
    # Skip files without important extensions (unless they're special files)
    if file_ext and file_ext not in IMPORTANT_EXTENSIONS and file_name not in ['Dockerfile', 'Makefile', 'requirements.txt']:
        return True
    
    # Skip hidden files (except .env.example)
    if file_name.startswith('.') and file_name != '.env.example':
        return True
    
    return False

def should_skip_dir(dir_name):
    """Check if a directory should be skipped."""
    return dir_name in SKIP_DIRS

def get_language_from_extension(file_path):
    """Get the language identifier for code blocks based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.json': 'json',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.toml': 'toml',
        '.sh': 'bash',
        '.sql': 'sql',
        '.md': 'markdown',
        '.txt': 'text',
        '.env': 'env',
        '.ini': 'ini',
        '.cfg': 'ini'
    }
    return language_map.get(ext, '')

def read_file_content(file_path):
    """Read file content safely."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except:
            return f"[Binary or unreadable file: {file_path}]"
    except Exception as e:
        return f"[Error reading file: {str(e)}]"

def generate_documentation(root_dir):
    """Generate project documentation."""
    documentation = []
    
    # Add header
    documentation.append("# Project Documentation\n")
    documentation.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    documentation.append("## Table of Contents\n")
    
    # Collect all files first for table of contents
    all_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Remove directories that should be skipped
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(file_path, root_dir)
            
            if not should_skip_file(file_path):
                all_files.append(relative_path)
    
    # Sort files for better organization
    all_files.sort()
    
    # Generate table of contents
    current_dir = None
    for file_path in all_files:
        dir_path = os.path.dirname(file_path)
        if dir_path != current_dir:
            current_dir = dir_path
            if dir_path:
                documentation.append(f"\n### {dir_path}/\n")
        
        file_name = os.path.basename(file_path)
        anchor = file_path.replace('/', '-').replace('.', '-').replace(' ', '-').lower()
        documentation.append(f"- [{file_name}](#{anchor})\n")
    
    documentation.append("\n---\n\n## File Contents\n")
    
    # Add file contents
    for relative_path in all_files:
        file_path = os.path.join(root_dir, relative_path)
        
        # Create section header
        anchor = relative_path.replace('/', '-').replace('.', '-').replace(' ', '-').lower()
        documentation.append(f"\n### {relative_path} {{#{anchor}}}\n")
        
        # Add file info
        file_size = os.path.getsize(file_path)
        documentation.append(f"**File Size:** {file_size} bytes\n")
        documentation.append(f"**File Path:** `{relative_path}`\n\n")
        
        # Read and add content
        content = read_file_content(file_path)
        language = get_language_from_extension(file_path)
        
        documentation.append(f"```{language}\n")
        documentation.append(content)
        documentation.append("\n```\n")
        documentation.append("\n---\n")
    
    return '\n'.join(documentation)

def main():
    """Main function to generate documentation."""
    # Get the current directory (where the script is run from)
    root_dir = os.getcwd()
    
    print(f"Generating documentation for: {root_dir}")
    print("This may take a moment...")
    
    # Generate documentation
    doc_content = generate_documentation(root_dir)
    
    # Write to file
    output_file = "project_documentation.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    # Calculate some statistics
    total_size = len(doc_content)
    line_count = doc_content.count('\n')
    
    print(f"\n✅ Documentation generated successfully!")
    print(f"📄 Output file: {output_file}")
    print(f"📊 Total size: {total_size:,} characters")
    print(f"📊 Total lines: {line_count:,}")
    
    # Show file count
    file_count = doc_content.count("### ")
    print(f"📊 Files documented: {file_count}")

if __name__ == "__main__":
    main()
