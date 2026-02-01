"""
Organizational Best Practices Module

Implements various file organization methodologies:
- Johnny Decimal: Hierarchical categorization with numeric IDs
- Zettelkasten: Knowledge management system with atomic notes
- PARA: Projects, Areas, Resources, Archives
- ACCESS: Activities, Clients, Courses, Events, Systems, Sources
- LATCH: Location, Alphabet, Time, Category, Hierarchy
"""

import os
import re
from datetime import datetime


class OrganizationalMethod:
    """Base class for organizational methods."""
    
    def __init__(self, name, description):
        self.name = name
        self.description = description
    
    def get_folder_structure(self, file_path, metadata=None):
        """
        Determine folder structure for a file.
        
        Args:
            file_path: Path to the file
            metadata: Optional metadata dictionary
            
        Returns:
            Relative folder path for the file
        """
        raise NotImplementedError


class JohnnyDecimalMethod(OrganizationalMethod):
    """
    Johnny Decimal System: Organize files in a 10-category hierarchical system.
    
    Format: XX.YY - Category.ID
    - 10-19: Personal
    - 20-29: Finance
    - 30-39: Work/Projects
    - 40-49: Reference/Learning
    - 50-59: Creative
    - 60-69: Technical
    - 70-79: Health
    - 80-89: Archive
    - 90-99: Miscellaneous
    """
    
    def __init__(self):
        super().__init__(
            "Johnny Decimal",
            "Hierarchical organization with numeric categories (10.01, 20.05, etc.)"
        )
        
        # Define category mappings
        self.categories = {
            'personal': '10-19',
            'finance': '20-29',
            'work': '30-39',
            'projects': '30-39',
            'reference': '40-49',
            'learning': '40-49',
            'education': '40-49',
            'creative': '50-59',
            'art': '50-59',
            'technical': '60-69',
            'code': '60-69',
            'health': '70-79',
            'medical': '70-79',
            'archive': '80-89',
            'misc': '90-99',
        }
        
        self.counters = {
            '10-19': 10,
            '20-29': 20,
            '30-39': 30,
            '40-49': 40,
            '50-59': 50,
            '60-69': 60,
            '70-79': 70,
            '80-89': 80,
            '90-99': 90,
        }
    
    def get_folder_structure(self, file_path, metadata=None):
        """Assign Johnny Decimal category based on file content/type."""
        ext = os.path.splitext(file_path)[1].lower()
        
        # Determine category based on file type and metadata
        if metadata and 'foldername' in metadata:
            folder = metadata['foldername'].lower()
            
            # Try to match with categories
            for key, category_range in self.categories.items():
                if key in folder:
                    base_num = int(category_range.split('-')[0])
                    return f"{base_num}.00"
        
        # Default categorization by file type
        if ext in ['.jpg', '.png', '.gif', '.svg', '.psd']:
            return "50.00/Images"  # Creative
        elif ext in ['.pdf', '.docx', '.txt', '.md']:
            return "40.00/Documents"  # Reference
        elif ext in ['.py', '.js', '.java', '.cpp']:
            return "60.00/Code"  # Technical
        elif ext in ['.xlsx', '.csv']:
            return "20.00/Spreadsheets"  # Finance
        else:
            return "90.00/Miscellaneous"  # Misc


class PARAMethod(OrganizationalMethod):
    """
    PARA Method: Projects, Areas, Resources, Archives
    
    - Projects: Short-term efforts with specific goals and deadlines
    - Areas: Long-term responsibilities to maintain
    - Resources: Topics of interest or useful information
    - Archives: Inactive items from the other categories
    """
    
    def __init__(self):
        super().__init__(
            "PARA",
            "Projects, Areas, Resources, Archives - productivity-focused organization"
        )
    
    def get_folder_structure(self, file_path, metadata=None):
        """Assign PARA category."""
        ext = os.path.splitext(file_path)[1].lower()
        basename = os.path.basename(file_path).lower()
        
        # Check for project indicators
        if any(word in basename for word in ['project', 'proposal', 'plan', 'draft']):
            return "1-Projects/Active"
        
        # Check for archive indicators (old files or specific archive keywords)
        # Consider files with years older than 3 years as potential archives
        current_year = datetime.now().year
        archive_years = [str(year) for year in range(current_year - 5, current_year - 2)]
        archive_keywords = ['old', 'backup', 'archive'] + archive_years
        if any(word in basename for word in archive_keywords):
            return "4-Archives"
        
        # Check metadata if available
        if metadata and 'foldername' in metadata:
            folder = metadata['foldername'].lower()
            
            if any(word in folder for word in ['work', 'project', 'task']):
                return "1-Projects/Active"
            elif any(word in folder for word in ['finance', 'health', 'personal']):
                return "2-Areas/" + folder.title()
            elif any(word in folder for word in ['reference', 'learn', 'tutorial', 'guide']):
                return "3-Resources/" + folder.title()
        
        # Default categorization
        if ext in ['.jpg', '.png', '.gif']:
            return "3-Resources/Media"
        elif ext in ['.pdf', '.docx', '.txt']:
            return "3-Resources/Documents"
        else:
            return "3-Resources/General"


class ACCESSMethod(OrganizationalMethod):
    """
    ACCESS Method: Activities, Clients, Courses, Events, Systems, Sources
    
    Designed for professional and educational contexts.
    """
    
    def __init__(self):
        super().__init__(
            "ACCESS",
            "Activities, Clients, Courses, Events, Systems, Sources"
        )
    
    def get_folder_structure(self, file_path, metadata=None):
        """Assign ACCESS category."""
        basename = os.path.basename(file_path).lower()
        
        # Activities
        if any(word in basename for word in ['meeting', 'task', 'todo', 'action']):
            return "Activities"
        
        # Clients
        if any(word in basename for word in ['client', 'customer', 'invoice', 'contract']):
            return "Clients"
        
        # Courses
        if any(word in basename for word in ['course', 'lesson', 'tutorial', 'lecture']):
            return "Courses"
        
        # Events
        if any(word in basename for word in ['event', 'conference', 'workshop', 'seminar']):
            return "Events"
        
        # Systems
        if any(word in basename for word in ['system', 'process', 'workflow', 'template']):
            return "Systems"
        
        # Sources (default for reference materials)
        return "Sources"


class ZettelkastenMethod(OrganizationalMethod):
    """
    Zettelkasten Method: Atomic notes with unique IDs and linking.
    
    Format: YYYYMMDDHHMMSS-title
    Each note is atomic and can link to others.
    """
    
    def __init__(self):
        super().__init__(
            "Zettelkasten",
            "Knowledge management with timestamped atomic notes"
        )
    
    def get_folder_structure(self, file_path, metadata=None):
        """Organize in flat structure with timestamps."""
        # Zettelkasten uses a flat structure with ID-based naming
        # All files go in the root with unique IDs
        return "Notes"


class LATCHMethod(OrganizationalMethod):
    """
    LATCH Method: Location, Alphabet, Time, Category, Hierarchy
    
    Organizes by the most natural access pattern for the content.
    """
    
    def __init__(self):
        super().__init__(
            "LATCH",
            "Location, Alphabet, Time, Category, Hierarchy"
        )
    
    def get_folder_structure(self, file_path, metadata=None):
        """Organize primarily by category and time."""
        ext = os.path.splitext(file_path)[1].lower()
        
        # Get file modification time
        try:
            mod_time = os.path.getmtime(file_path)
            year = datetime.fromtimestamp(mod_time).strftime('%Y')
        except (OSError, ValueError):
            year = 'Unknown'
        
        # Category-based organization with time hierarchy
        if ext in ['.jpg', '.png', '.gif', '.bmp']:
            return f"Images/{year}"
        elif ext in ['.pdf', '.docx', '.txt', '.md']:
            return f"Documents/{year}"
        elif ext in ['.mp3', '.wav', '.flac']:
            return f"Audio/{year}"
        elif ext in ['.mp4', '.avi', '.mkv']:
            return f"Video/{year}"
        else:
            return f"Other/{year}"


# Registry of available methods
ORGANIZATIONAL_METHODS = {
    'johnny_decimal': JohnnyDecimalMethod(),
    'para': PARAMethod(),
    'access': ACCESSMethod(),
    'zettelkasten': ZettelkastenMethod(),
    'latch': LATCHMethod(),
}


def get_method(method_name):
    """Get organizational method by name."""
    return ORGANIZATIONAL_METHODS.get(method_name.lower())


def list_methods():
    """List all available organizational methods."""
    return [
        {
            'key': key,
            'name': method.name,
            'description': method.description
        }
        for key, method in ORGANIZATIONAL_METHODS.items()
    ]


def apply_organizational_method(file_paths, output_path, method_name, metadata_dict=None):
    """
    Apply an organizational method to files.
    
    Args:
        file_paths: List of file paths
        output_path: Output directory
        method_name: Name of organizational method
        metadata_dict: Optional dictionary mapping file_path to metadata
        
    Returns:
        List of file operations
    """
    method = get_method(method_name)
    if not method:
        raise ValueError(f"Unknown organizational method: {method_name}")
    
    operations = []
    
    for file_path in file_paths:
        # Get metadata if available
        metadata = metadata_dict.get(file_path) if metadata_dict else None
        
        # Determine folder structure
        folder_structure = method.get_folder_structure(file_path, metadata)
        
        # Create destination path
        file_name = os.path.basename(file_path)
        destination = os.path.join(output_path, folder_structure, file_name)
        
        operations.append({
            'source': file_path,
            'destination': destination,
            'link_type': 'hardlink'
        })
    
    return operations
