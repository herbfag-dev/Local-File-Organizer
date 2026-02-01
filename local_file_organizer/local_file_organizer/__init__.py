"""Local File Organizer - Beautiful Reflex GUI with Material Design"""

import reflex as rx
from typing import List, Dict, Optional
import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import existing functionality
try:
    from file_utils import (
        collect_file_paths,
        separate_files_by_type,
        read_file_data
    )
    from data_processing_common import (
        compute_operations,
        execute_operations,
        process_files_by_date,
        process_files_by_type,
    )
    from text_data_processing import process_text_files
    from image_data_processing import process_image_files
    from output_filter import filter_specific_output
    from nexa.gguf import NexaVLMInference, NexaTextInference
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import all modules: {e}")
    MODELS_AVAILABLE = False


class FileOrganizerState(rx.State):
    """State management for the File Organizer application."""
    
    # UI State
    current_step: int = 0
    is_processing: bool = False
    progress: int = 0
    progress_text: str = ""
    
    # File paths
    input_path: str = ""
    output_path: str = ""
    
    # Organization mode
    organization_mode: str = "content"  # content, date, type
    
    # Silent mode
    silent_mode: bool = False
    
    # File information
    total_files: int = 0
    file_list: List[str] = []
    
    # Operations
    operations: List[Dict] = []
    proposed_structure: str = ""
    
    # Models (class variables to persist across state instances)
    _image_inference = None
    _text_inference = None
    
    # Status messages
    status_message: str = ""
    error_message: str = ""
    
    def set_input_path(self, path: str):
        """Set and validate input path."""
        self.input_path = path
        if os.path.exists(path):
            self.error_message = ""
            self.status_message = f"✓ Valid directory: {path}"
        else:
            self.error_message = f"✗ Directory not found: {path}"
            self.status_message = ""
    
    def set_output_path(self, path: str):
        """Set output path."""
        if not path:
            # Default to organized_folder in input directory's parent
            if self.input_path:
                self.output_path = os.path.join(
                    os.path.dirname(self.input_path), 
                    'organized_folder'
                )
        else:
            self.output_path = path
        self.status_message = f"✓ Output will be saved to: {self.output_path}"
    
    def set_organization_mode(self, mode: str):
        """Set the organization mode."""
        self.organization_mode = mode
        mode_names = {
            "content": "AI Content Analysis",
            "date": "Date-based Organization", 
            "type": "File Type Organization"
        }
        self.status_message = f"✓ Selected: {mode_names.get(mode, mode)}"
    
    def toggle_silent_mode(self):
        """Toggle silent mode."""
        self.silent_mode = not self.silent_mode
    
    def reset_to_start(self):
        """Reset the app to start a new organization."""
        self.current_step = 0
        self.input_path = ""
        self.output_path = ""
        self.status_message = ""
        self.error_message = ""
        self.file_list = []
        self.total_files = 0
        self.operations = []
        self.proposed_structure = ""
    
    def next_step(self):
        """Move to next step."""
        if self.current_step < 3:
            self.current_step += 1
    
    def prev_step(self):
        """Move to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
    
    async def scan_files(self):
        """Scan files in the input directory."""
        if not self.input_path or not os.path.exists(self.input_path):
            self.error_message = "Please enter a valid input directory"
            return
        
        self.is_processing = True
        self.progress = 10
        self.progress_text = "Scanning directory..."
        
        try:
            # Collect file paths
            file_paths = collect_file_paths(self.input_path)
            self.file_list = file_paths
            self.total_files = len(file_paths)
            
            # Set default output path if not set
            if not self.output_path:
                self.set_output_path("")
            
            self.progress = 100
            self.progress_text = f"Found {self.total_files} files"
            self.status_message = f"✓ Scanned {self.total_files} files successfully"
            self.error_message = ""
            
            # Move to next step
            yield
            await asyncio.sleep(0.5)
            self.next_step()
            
        except Exception as e:
            self.error_message = f"Error scanning files: {str(e)}"
            self.status_message = ""
        finally:
            self.is_processing = False
            self.progress = 0
    
    def initialize_models(self):
        """Initialize AI models if not already initialized."""
        if FileOrganizerState._image_inference is None:
            model_path = "llava-v1.6-vicuna-7b:q4_0"
            model_path_text = "Llama3.2-3B-Instruct:q3_K_M"
            
            with filter_specific_output():
                FileOrganizerState._image_inference = NexaVLMInference(
                    model_path=model_path,
                    local_path=None,
                    stop_words=[],
                    temperature=0.3,
                    max_new_tokens=3000,
                    top_k=3,
                    top_p=0.2,
                    profiling=False
                )
                
                FileOrganizerState._text_inference = NexaTextInference(
                    model_path=model_path_text,
                    local_path=None,
                    stop_words=[],
                    temperature=0.5,
                    max_new_tokens=3000,
                    top_k=3,
                    top_p=0.3,
                    profiling=False
                )
    
    async def organize_files(self):
        """Organize files based on selected mode."""
        self.is_processing = True
        self.progress = 0
        self.progress_text = "Preparing to organize files..."
        
        try:
            if self.organization_mode == "content":
                # Initialize models
                self.progress = 10
                self.progress_text = "Loading AI models..."
                yield
                
                self.initialize_models()
                
                # Separate files
                self.progress = 20
                self.progress_text = "Categorizing files..."
                yield
                
                image_files, text_files = separate_files_by_type(self.file_list)
                
                # Process text files
                self.progress = 40
                self.progress_text = f"Analyzing {len(text_files)} text files..."
                yield
                
                text_tuples = []
                for fp in text_files:
                    text_content = read_file_data(fp)
                    if text_content:
                        text_tuples.append((fp, text_content))
                
                data_texts = process_text_files(
                    text_tuples, 
                    FileOrganizerState._text_inference, 
                    silent=True, 
                    log_file=None
                )
                
                # Process image files
                self.progress = 60
                self.progress_text = f"Analyzing {len(image_files)} image files..."
                yield
                
                data_images = process_image_files(
                    image_files, 
                    FileOrganizerState._image_inference,
                    FileOrganizerState._text_inference,
                    silent=True,
                    log_file=None
                )
                
                # Compute operations
                self.progress = 80
                self.progress_text = "Computing file operations..."
                yield
                
                all_data = data_images + data_texts
                renamed_files = set()
                processed_files = set()
                
                self.operations = compute_operations(
                    all_data,
                    self.output_path,
                    renamed_files,
                    processed_files
                )
                
            elif self.organization_mode == "date":
                self.progress = 50
                self.progress_text = "Organizing by date..."
                yield
                
                self.operations = process_files_by_date(
                    self.file_list,
                    self.output_path,
                    dry_run=False,
                    silent=True,
                    log_file=None
                )
                
            elif self.organization_mode == "type":
                self.progress = 50
                self.progress_text = "Organizing by file type..."
                yield
                
                self.operations = process_files_by_type(
                    self.file_list,
                    self.output_path,
                    dry_run=False,
                    silent=True,
                    log_file=None
                )
            
            # Generate proposed structure
            self.progress = 90
            self.progress_text = "Generating preview..."
            yield
            
            self.proposed_structure = self._generate_structure_preview()
            
            self.progress = 100
            self.progress_text = "Ready to organize!"
            self.status_message = f"✓ Ready to organize {len(self.operations)} files"
            
            # Move to preview step
            yield
            await asyncio.sleep(0.5)
            self.next_step()
            
        except Exception as e:
            self.error_message = f"Error organizing files: {str(e)}"
            self.status_message = ""
        finally:
            self.is_processing = False
    
    def _generate_structure_preview(self) -> str:
        """Generate a preview of the proposed directory structure."""
        tree = {}
        for op in self.operations:
            rel_path = os.path.relpath(op['destination'], self.output_path)
            parts = rel_path.split(os.sep)
            current_level = tree
            for part in parts:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
        
        lines = [self.output_path]
        self._format_tree(tree, lines)
        return "\n".join(lines)
    
    def _format_tree(self, tree: dict, lines: list, prefix: str = ""):
        """Format directory tree for display."""
        items = list(tree.items())
        for i, (key, value) in enumerate(items):
            is_last = i == len(items) - 1
            pointer = "└── " if is_last else "├── "
            lines.append(prefix + pointer + key)
            if value:
                extension = "    " if is_last else "│   "
                self._format_tree(value, lines, prefix + extension)
    
    async def execute_organization(self):
        """Execute the file organization operations."""
        self.is_processing = True
        self.progress = 0
        self.progress_text = "Creating output directory..."
        
        try:
            # Create output directory
            os.makedirs(self.output_path, exist_ok=True)
            
            self.progress = 20
            self.progress_text = "Organizing files..."
            yield
            
            # Execute operations
            execute_operations(
                self.operations,
                dry_run=False,
                silent=True,
                log_file=None
            )
            
            self.progress = 100
            self.progress_text = "Complete!"
            self.status_message = f"✓ Successfully organized {len(self.operations)} files!"
            
        except Exception as e:
            self.error_message = f"Error executing operations: {str(e)}"
            self.status_message = ""
        finally:
            self.is_processing = False


def index() -> rx.Component:
    """Main page component."""
    return rx.box(
        # Header
        rx.box(
            rx.hstack(
                rx.icon("folder-tree", size=32, color="#6366f1"),
                rx.vstack(
                    rx.heading(
                        "Local File Organizer",
                        size="8",
                        weight="bold",
                        color="#1e293b",
                    ),
                    rx.text(
                        "AI-powered file organization on your device",
                        size="3",
                        color="#64748b",
                    ),
                    spacing="1",
                    align="start",
                ),
                spacing="4",
                align="center",
            ),
            padding="2rem",
            background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            border_radius="0 0 24px 24px",
            box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.1)",
        ),
        
        # Main content
        rx.container(
            rx.vstack(
                # Step indicator
                step_indicator(),
                
                # Content based on current step
                rx.cond(
                    FileOrganizerState.current_step == 0,
                    step_1_select_directory(),
                ),
                rx.cond(
                    FileOrganizerState.current_step == 1,
                    step_2_choose_mode(),
                ),
                rx.cond(
                    FileOrganizerState.current_step == 2,
                    step_3_preview(),
                ),
                rx.cond(
                    FileOrganizerState.current_step == 3,
                    step_4_complete(),
                ),
                
                spacing="6",
                width="100%",
            ),
            max_width="1200px",
            padding="2rem",
        ),
        
        # Footer
        rx.box(
            rx.text(
                "100% Privacy • All Processing Happens Locally",
                size="2",
                color="#64748b",
                text_align="center",
            ),
            padding="2rem",
            border_top="1px solid #e2e8f0",
        ),
        
        width="100%",
        min_height="100vh",
        background="#f8fafc",
    )


def step_indicator() -> rx.Component:
    """Visual step indicator."""
    steps = [
        {"num": 1, "title": "Select Directory", "icon": "folder"},
        {"num": 2, "title": "Choose Mode", "icon": "settings"},
        {"num": 3, "title": "Preview", "icon": "eye"},
        {"num": 4, "title": "Complete", "icon": "circle-check"},
    ]
    
    return rx.box(
        rx.hstack(
            *[
                rx.hstack(
                    # Step circle
                    rx.box(
                        rx.cond(
                            FileOrganizerState.current_step >= i,
                            rx.icon(step["icon"], size=20, color="white"),
                            rx.text(str(step["num"]), color="white", weight="bold"),
                        ),
                        width="48px",
                        height="48px",
                        border_radius="50%",
                        background=rx.cond(
                            FileOrganizerState.current_step >= i,
                            "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                            "#cbd5e1",
                        ),
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        transition="all 0.3s ease",
                        box_shadow=rx.cond(
                            FileOrganizerState.current_step >= i,
                            "0 4px 6px -1px rgba(102, 126, 234, 0.3)",
                            "none",
                        ),
                    ),
                    # Step label
                    rx.text(
                        step["title"],
                        size="2",
                        weight="medium",
                        color=rx.cond(
                            FileOrganizerState.current_step >= i,
                            "#1e293b",
                            "#94a3b8",
                        ),
                        display=["none", "none", "block"],
                    ),
                    # Connector line (except for last step)
                    rx.cond(
                        i < len(steps) - 1,
                        rx.box(
                            width=["40px", "60px", "100px"],
                            height="2px",
                            background=rx.cond(
                                FileOrganizerState.current_step > i,
                                "#667eea",
                                "#e2e8f0",
                            ),
                            transition="all 0.3s ease",
                        ),
                    ),
                    spacing="3",
                    align="center",
                )
                for i, step in enumerate(steps)
            ],
            spacing="0",
            justify="center",
            align="center",
            width="100%",
        ),
        padding="2rem",
        background="white",
        border_radius="16px",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.1)",
    )


def step_1_select_directory() -> rx.Component:
    """Step 1: Select directory to organize."""
    return rx.vstack(
        rx.box(
            rx.vstack(
                rx.heading(
                    "Select Directory to Organize",
                    size="7",
                    weight="bold",
                    color="#1e293b",
                ),
                rx.text(
                    "Choose the folder containing files you want to organize",
                    size="3",
                    color="#64748b",
                ),
                spacing="2",
            ),
            padding_bottom="1.5rem",
        ),
        
        # Input path
        rx.vstack(
            rx.text("Input Directory", size="3", weight="medium", color="#475569"),
            rx.input(
                placeholder="/path/to/messy/folder",
                value=FileOrganizerState.input_path,
                on_change=FileOrganizerState.set_input_path,
                size="3",
                width="100%",
                border_radius="8px",
            ),
            spacing="2",
            width="100%",
        ),
        
        # Output path
        rx.vstack(
            rx.text("Output Directory (optional)", size="3", weight="medium", color="#475569"),
            rx.input(
                placeholder="Leave empty for default (organized_folder)",
                value=FileOrganizerState.output_path,
                on_change=FileOrganizerState.set_output_path,
                size="3",
                width="100%",
                border_radius="8px",
            ),
            rx.text(
                "💡 Default: organized_folder in the same parent directory",
                size="2",
                color="#94a3b8",
            ),
            spacing="2",
            width="100%",
        ),
        
        # Status messages
        rx.cond(
            FileOrganizerState.status_message != "",
            rx.box(
                rx.hstack(
                    rx.icon("circle-check", size=20, color="#10b981"),
                    rx.text(FileOrganizerState.status_message, size="2", color="#059669"),
                    spacing="2",
                ),
                padding="1rem",
                background="#d1fae5",
                border_radius="8px",
                border="1px solid #6ee7b7",
            ),
        ),
        
        rx.cond(
            FileOrganizerState.error_message != "",
            rx.box(
                rx.hstack(
                    rx.icon("circle-alert", size=20, color="#ef4444"),
                    rx.text(FileOrganizerState.error_message, size="2", color="#dc2626"),
                    spacing="2",
                ),
                padding="1rem",
                background="#fee2e2",
                border_radius="8px",
                border="1px solid #fca5a5",
            ),
        ),
        
        # Progress bar
        rx.cond(
            FileOrganizerState.is_processing,
            rx.vstack(
                rx.progress(
                    value=FileOrganizerState.progress,
                    max=100,
                    width="100%",
                    height="8px",
                    color_scheme="purple",
                ),
                rx.text(
                    FileOrganizerState.progress_text,
                    size="2",
                    color="#64748b",
                ),
                spacing="2",
                width="100%",
            ),
        ),
        
        # Action button
        rx.hstack(
            rx.button(
                rx.icon("scan", margin_right="0.5rem"),
                "Scan Directory",
                size="3",
                on_click=FileOrganizerState.scan_files,
                disabled=FileOrganizerState.is_processing,
                background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                color="white",
                border_radius="8px",
                padding="0.75rem 2rem",
                cursor="pointer",
                _hover={"transform": "translateY(-2px)", "box_shadow": "0 10px 15px -3px rgba(102, 126, 234, 0.3)"},
                transition="all 0.3s ease",
            ),
            justify="center",
            width="100%",
            padding_top="1rem",
        ),
        
        spacing="6",
        width="100%",
        padding="2rem",
        background="white",
        border_radius="16px",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.1)",
    )


def step_2_choose_mode() -> rx.Component:
    """Step 2: Choose organization mode."""
    return rx.vstack(
        rx.box(
            rx.vstack(
                rx.heading(
                    "Choose Organization Mode",
                    size="7",
                    weight="bold",
                    color="#1e293b",
                ),
                rx.text(
                    f"Found {FileOrganizerState.total_files} files ready to organize",
                    size="3",
                    color="#64748b",
                ),
                spacing="2",
            ),
            padding_bottom="1.5rem",
        ),
        
        # Mode selection cards
        rx.grid(
            # Content mode
            mode_card(
                "content",
                "AI Content Analysis",
                "Uses AI to understand your files and organize them by content",
                "brain",
                "#8b5cf6",
                ["Smart categorization", "Automatic naming", "Context-aware"]
            ),
            
            # Date mode
            mode_card(
                "date",
                "Date-based Organization",
                "Organize files by creation or modification date",
                "calendar",
                "#06b6d4",
                ["By year/month", "Timeline view", "Fast processing"]
            ),
            
            # Type mode
            mode_card(
                "type",
                "File Type Organization",
                "Group files by their type and extension",
                "file-type",
                "#f59e0b",
                ["By extension", "Simple structure", "Instant results"]
            ),
            
            columns=rx.breakpoints(initial="1", sm="2", md="3"),
            spacing="4",
            width="100%",
        ),
        
        # Status message
        rx.cond(
            FileOrganizerState.status_message != "",
            rx.box(
                rx.hstack(
                    rx.icon("circle-check", size=20, color="#10b981"),
                    rx.text(FileOrganizerState.status_message, size="2", color="#059669"),
                    spacing="2",
                ),
                padding="1rem",
                background="#d1fae5",
                border_radius="8px",
                border="1px solid #6ee7b7",
            ),
        ),
        
        # Progress bar
        rx.cond(
            FileOrganizerState.is_processing,
            rx.vstack(
                rx.progress(
                    value=FileOrganizerState.progress,
                    max=100,
                    width="100%",
                    height="8px",
                    color_scheme="purple",
                ),
                rx.text(
                    FileOrganizerState.progress_text,
                    size="2",
                    color="#64748b",
                ),
                spacing="2",
                width="100%",
            ),
        ),
        
        # Action buttons
        rx.hstack(
            rx.button(
                rx.icon("arrow-left", margin_right="0.5rem"),
                "Back",
                size="3",
                on_click=FileOrganizerState.prev_step,
                variant="outline",
                color_scheme="gray",
                border_radius="8px",
                padding="0.75rem 2rem",
            ),
            rx.button(
                rx.icon("wand", margin_right="0.5rem"),
                "Organize Files",
                size="3",
                on_click=FileOrganizerState.organize_files,
                disabled=FileOrganizerState.is_processing,
                background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                color="white",
                border_radius="8px",
                padding="0.75rem 2rem",
                cursor="pointer",
                _hover={"transform": "translateY(-2px)", "box_shadow": "0 10px 15px -3px rgba(102, 126, 234, 0.3)"},
                transition="all 0.3s ease",
            ),
            justify="between",
            width="100%",
            padding_top="1rem",
        ),
        
        spacing="6",
        width="100%",
        padding="2rem",
        background="white",
        border_radius="16px",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.1)",
    )


def mode_card(mode_id: str, title: str, description: str, icon: str, color: str, features: list) -> rx.Component:
    """Card for selecting organization mode."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=28, color=color),
                rx.heading(title, size="5", weight="bold", color="#1e293b"),
                spacing="3",
                align="center",
            ),
            rx.text(description, size="2", color="#64748b", line_height="1.6"),
            rx.vstack(
                *[
                    rx.hstack(
                        rx.icon("check", size=16, color=color),
                        rx.text(feature, size="2", color="#475569"),
                        spacing="2",
                    )
                    for feature in features
                ],
                spacing="2",
                align="start",
                width="100%",
            ),
            spacing="4",
            align="start",
        ),
        on_click=FileOrganizerState.set_organization_mode(mode_id),
        padding="1.5rem",
        background=rx.cond(
            FileOrganizerState.organization_mode == mode_id,
            f"{color}10",
            "white"
        ),
        border=rx.cond(
            FileOrganizerState.organization_mode == mode_id,
            f"2px solid {color}",
            "2px solid #e2e8f0"
        ),
        border_radius="12px",
        cursor="pointer",
        transition="all 0.3s ease",
        _hover={
            "transform": "translateY(-4px)",
            "box_shadow": f"0 10px 15px -3px {color}30",
        },
    )


def step_3_preview() -> rx.Component:
    """Step 3: Preview proposed organization."""
    return rx.vstack(
        rx.box(
            rx.vstack(
                rx.heading(
                    "Preview Proposed Structure",
                    size="7",
                    weight="bold",
                    color="#1e293b",
                ),
                rx.text(
                    "Review how your files will be organized",
                    size="3",
                    color="#64748b",
                ),
                spacing="2",
            ),
            padding_bottom="1.5rem",
        ),
        
        # Stats
        rx.grid(
            stat_card("Files to Organize", FileOrganizerState.total_files, "files", "#8b5cf6"),
            stat_card("Operations", FileOrganizerState.operations.length(), "git-branch", "#06b6d4"),
            stat_card("Mode", FileOrganizerState.organization_mode.capitalize(), "settings", "#f59e0b"),
            columns=rx.breakpoints(initial="1", md="3"),
            spacing="4",
            width="100%",
        ),
        
        # Structure preview
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("folder-tree", size=20, color="#6366f1"),
                    rx.heading("Directory Structure", size="4", weight="bold", color="#1e293b"),
                    spacing="2",
                ),
                rx.box(
                    rx.text(
                        FileOrganizerState.proposed_structure,
                        font_family="monospace",
                        white_space="pre",
                        size="2",
                        width="100%",
                    ),
                    max_height="400px",
                    overflow_y="auto",
                    width="100%",
                    padding="1rem",
                    background="#f8f9fa",
                    border_radius="8px",
                    border="1px solid #e2e8f0",
                ),
                spacing="4",
                width="100%",
            ),
            padding="1.5rem",
            background="#fafafa",
            border_radius="12px",
            border="1px solid #e2e8f0",
        ),
        
        # Progress bar
        rx.cond(
            FileOrganizerState.is_processing,
            rx.vstack(
                rx.progress(
                    value=FileOrganizerState.progress,
                    max=100,
                    width="100%",
                    height="8px",
                    color_scheme="purple",
                ),
                rx.text(
                    FileOrganizerState.progress_text,
                    size="2",
                    color="#64748b",
                ),
                spacing="2",
                width="100%",
            ),
        ),
        
        # Action buttons
        rx.hstack(
            rx.button(
                rx.icon("arrow-left", margin_right="0.5rem"),
                "Back",
                size="3",
                on_click=FileOrganizerState.prev_step,
                variant="outline",
                color_scheme="gray",
                border_radius="8px",
                padding="0.75rem 2rem",
            ),
            rx.button(
                rx.icon("rocket", margin_right="0.5rem"),
                "Execute Organization",
                size="3",
                on_click=FileOrganizerState.execute_organization,
                disabled=FileOrganizerState.is_processing,
                background="linear-gradient(135deg, #10b981 0%, #059669 100%)",
                color="white",
                border_radius="8px",
                padding="0.75rem 2rem",
                cursor="pointer",
                _hover={"transform": "translateY(-2px)", "box_shadow": "0 10px 15px -3px rgba(16, 185, 129, 0.3)"},
                transition="all 0.3s ease",
            ),
            justify="between",
            width="100%",
            padding_top="1rem",
        ),
        
        spacing="6",
        width="100%",
        padding="2rem",
        background="white",
        border_radius="16px",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.1)",
    )


def stat_card(label: str, value: str, icon: str, color: str) -> rx.Component:
    """Statistics card component."""
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon(icon, size=24, color=color),
                padding="0.75rem",
                background=f"{color}20",
                border_radius="8px",
            ),
            rx.vstack(
                rx.text(label, size="2", color="#64748b"),
                rx.text(value, size="5", weight="bold", color="#1e293b"),
                spacing="0",
                align="start",
            ),
            spacing="3",
            align="center",
        ),
        padding="1.25rem",
        background="white",
        border_radius="12px",
        border="1px solid #e2e8f0",
    )


def step_4_complete() -> rx.Component:
    """Step 4: Completion screen."""
    return rx.vstack(
        rx.box(
            rx.vstack(
                rx.box(
                    rx.icon(
                        "circle-check",
                        size=64,
                        color="#10b981",
                    ),
                    display="flex",
                    justify_content="center",
                    width="100%",
                ),
                rx.heading(
                    "Organization Complete!",
                    size="8",
                    weight="bold",
                    color="#1e293b",
                    text_align="center",
                ),
                rx.text(
                    FileOrganizerState.status_message,
                    size="4",
                    color="#64748b",
                    text_align="center",
                ),
                spacing="4",
                align="center",
            ),
        ),
        
        # Success message
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("folder-check", size=24, color="#059669"),
                    rx.heading("Files Organized Successfully", size="4", weight="bold", color="#1e293b"),
                    spacing="2",
                ),
                rx.text(
                    f"Your {FileOrganizerState.total_files} files have been organized in:",
                    size="3",
                    color="#475569",
                ),
                rx.code(FileOrganizerState.output_path, color_scheme="green"),
                spacing="3",
            ),
            padding="2rem",
            background="linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)",
            border_radius="16px",
            border="2px solid #6ee7b7",
        ),
        
        # Action buttons
        rx.hstack(
            rx.button(
                rx.icon("refresh-cw", margin_right="0.5rem"),
                "Organize Another Folder",
                size="3",
                on_click=FileOrganizerState.reset_to_start,
                background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                color="white",
                border_radius="8px",
                padding="0.75rem 2rem",
                cursor="pointer",
                _hover={"transform": "translateY(-2px)", "box_shadow": "0 10px 15px -3px rgba(102, 126, 234, 0.3)"},
                transition="all 0.3s ease",
            ),
            justify="center",
            width="100%",
            padding_top="1rem",
            spacing="4",
        ),
        
        spacing="6",
        width="100%",
        padding="2rem",
        background="white",
        border_radius="16px",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.1)",
    )


# App configuration
app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="violet",
        radius="large",
    ),
)
app.add_page(index, route="/", title="Local File Organizer")
