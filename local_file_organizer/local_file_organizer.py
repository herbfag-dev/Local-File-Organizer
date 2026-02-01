"""
Local File Organizer - Reflex GUI Dashboard
Modern web-based interface for AI-powered file organization
"""

import reflex as rx
import os
import sys
import time
import asyncio
from typing import List, Dict, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from file_utils import (
    display_directory_tree,
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

# Try to import Nexa models, but make them optional for GUI startup
try:
    from nexa.gguf import NexaVLMInference, NexaTextInference
    NEXA_AVAILABLE = True
except ImportError:
    NEXA_AVAILABLE = False
    NexaVLMInference = None
    NexaTextInference = None


class State(rx.State):
    """Application state for the File Organizer."""
    
    # Path configuration
    input_path: str = ""
    output_path: str = ""
    
    # Mode selection
    selected_mode: str = "content"
    
    # Processing state
    is_processing: bool = False
    processing_progress: int = 0
    processing_status: str = ""
    
    # File lists
    file_list: List[str] = []
    file_count: int = 0
    
    # Operations
    operations: List[Dict] = []
    simulated_tree: str = ""
    
    # Models
    models_initialized: bool = False
    
    # Settings
    silent_mode: bool = False
    dry_run_mode: bool = True
    
    # UI State
    show_settings: bool = False
    show_preview: bool = False
    selected_file_preview: str = ""
    
    # Logs
    log_messages: List[str] = []
    
    # Model references (not serializable, so we'll handle them separately)
    _image_inference = None
    _text_inference = None
    
    def add_log(self, message: str):
        """Add a log message."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {message}")
        
    def clear_logs(self):
        """Clear all log messages."""
        self.log_messages = []
    
    def set_input_path(self, path: str):
        """Set and validate input path."""
        self.input_path = path.strip()
        if os.path.exists(self.input_path):
            self.add_log(f"✓ Input path set: {self.input_path}")
            # Auto-set output path if not set
            if not self.output_path:
                parent_dir = os.path.dirname(self.input_path)
                self.output_path = os.path.join(parent_dir, 'organized_folder')
                self.add_log(f"✓ Auto-set output path: {self.output_path}")
            # Load file list
            self.load_files()
        else:
            self.add_log(f"✗ Invalid input path: {self.input_path}")
    
    def set_output_path(self, path: str):
        """Set output path."""
        self.output_path = path.strip()
        self.add_log(f"✓ Output path set: {self.output_path}")
    
    def set_mode(self, mode: str):
        """Set processing mode."""
        self.selected_mode = mode
        self.add_log(f"Mode selected: {mode}")
    
    def toggle_settings(self):
        """Toggle settings panel."""
        self.show_settings = not self.show_settings
    
    def set_silent_mode(self, value: bool):
        """Set silent mode."""
        self.silent_mode = value
        self.add_log(f"Silent mode: {'enabled' if value else 'disabled'}")
    
    def load_files(self):
        """Load files from input path."""
        if not os.path.exists(self.input_path):
            self.add_log("✗ Cannot load files: Invalid input path")
            return
        
        try:
            self.file_list = collect_file_paths(self.input_path)
            self.file_count = len(self.file_list)
            self.add_log(f"✓ Loaded {self.file_count} files from input directory")
        except Exception as e:
            self.add_log(f"✗ Error loading files: {str(e)}")
    
    async def initialize_models(self):
        """Initialize AI models."""
        if self.models_initialized:
            return
        
        if not NEXA_AVAILABLE:
            self.add_log("✗ Nexa SDK not available. Please install it to use content mode.")
            self.processing_status = "Nexa SDK not installed"
            return
        
        self.add_log("Initializing AI models...")
        self.processing_status = "Initializing models..."
        
        try:
            model_path = "llava-v1.6-vicuna-7b:q4_0"
            model_path_text = "Llama3.2-3B-Instruct:q3_K_M"
            
            # Initialize models (this is synchronous in the actual implementation)
            self._image_inference = NexaVLMInference(
                model_path=model_path,
                local_path=None,
                stop_words=[],
                temperature=0.3,
                max_new_tokens=3000,
                top_k=3,
                top_p=0.2,
                profiling=False
            )
            
            self._text_inference = NexaTextInference(
                model_path=model_path_text,
                local_path=None,
                stop_words=[],
                temperature=0.5,
                max_new_tokens=3000,
                top_k=3,
                top_p=0.3,
                profiling=False
            )
            
            self.models_initialized = True
            self.add_log("✓ Models initialized successfully")
            self.processing_status = "Models ready"
        except Exception as e:
            self.add_log(f"✗ Error initializing models: {str(e)}")
            self.processing_status = "Model initialization failed"
    
    async def process_files(self):
        """Process files based on selected mode."""
        if not self.input_path or not os.path.exists(self.input_path):
            self.add_log("✗ Please set a valid input path")
            return
        
        if not self.output_path:
            self.add_log("✗ Please set an output path")
            return
        
        self.is_processing = True
        self.processing_progress = 0
        self.processing_status = "Starting..."
        self.clear_logs()
        self.add_log(f"Starting file organization in '{self.selected_mode}' mode")
        
        try:
            if self.selected_mode == "content":
                await self.process_content_mode()
            elif self.selected_mode == "date":
                await self.process_date_mode()
            elif self.selected_mode == "type":
                await self.process_type_mode()
            
            self.processing_status = "Complete!"
            self.add_log("✓ Processing complete!")
        except Exception as e:
            self.processing_status = f"Error: {str(e)}"
            self.add_log(f"✗ Error during processing: {str(e)}")
        finally:
            self.is_processing = False
            self.processing_progress = 100
    
    async def process_content_mode(self):
        """Process files using content analysis."""
        # Check if Nexa is available
        if not NEXA_AVAILABLE:
            self.add_log("✗ Content mode requires Nexa SDK. Please install it first.")
            self.processing_status = "Nexa SDK required"
            return
        
        # Initialize models if needed
        if not self.models_initialized:
            await self.initialize_models()
        
        if not self.models_initialized:
            self.add_log("✗ Cannot proceed without initialized models")
            return
        
        self.processing_status = "Analyzing files..."
        self.processing_progress = 10
        
        # Separate files by type
        image_files, text_files = separate_files_by_type(self.file_list)
        self.add_log(f"Found {len(image_files)} images and {len(text_files)} text files")
        
        # Process text files
        self.processing_status = "Processing text files..."
        self.processing_progress = 30
        text_tuples = []
        for fp in text_files:
            text_content = read_file_data(fp)
            if text_content is not None:
                text_tuples.append((fp, text_content))
        
        data_texts = process_text_files(
            text_tuples, 
            self._text_inference, 
            silent=self.silent_mode, 
            log_file=None
        )
        
        # Process image files
        self.processing_status = "Processing images..."
        self.processing_progress = 60
        data_images = process_image_files(
            image_files, 
            self._image_inference, 
            self._text_inference, 
            silent=self.silent_mode, 
            log_file=None
        )
        
        # Compute operations
        self.processing_status = "Computing operations..."
        self.processing_progress = 80
        all_data = data_images + data_texts
        renamed_files = set()
        processed_files = set()
        
        self.operations = compute_operations(
            all_data,
            self.output_path,
            renamed_files,
            processed_files
        )
        
        self.add_log(f"✓ Generated {len(self.operations)} file operations")
        self.generate_simulated_tree()
    
    async def process_date_mode(self):
        """Process files by date."""
        self.processing_status = "Organizing by date..."
        self.processing_progress = 50
        
        self.operations = process_files_by_date(
            self.file_list,
            self.output_path,
            dry_run=False,
            silent=self.silent_mode,
            log_file=None
        )
        
        self.add_log(f"✓ Generated {len(self.operations)} file operations")
        self.generate_simulated_tree()
    
    async def process_type_mode(self):
        """Process files by type."""
        self.processing_status = "Organizing by type..."
        self.processing_progress = 50
        
        self.operations = process_files_by_type(
            self.file_list,
            self.output_path,
            dry_run=False,
            silent=self.silent_mode,
            log_file=None
        )
        
        self.add_log(f"✓ Generated {len(self.operations)} file operations")
        self.generate_simulated_tree()
    
    def generate_simulated_tree(self):
        """Generate a simulated directory tree from operations."""
        tree = {}
        for op in self.operations:
            rel_path = os.path.relpath(op['destination'], self.output_path)
            parts = rel_path.split(os.sep)
            current_level = tree
            for part in parts:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
        
        # Convert tree to string representation
        self.simulated_tree = self._tree_to_string(tree)
    
    def _tree_to_string(self, tree, prefix='', is_last=True):
        """Convert tree dict to string representation."""
        if not tree:
            return ""
        
        result = []
        items = list(tree.items())
        for i, (key, subtree) in enumerate(items):
            is_last_item = (i == len(items) - 1)
            pointer = '└── ' if is_last_item else '├── '
            result.append(prefix + pointer + key)
            
            if subtree:
                extension = '    ' if is_last_item else '│   '
                result.append(self._tree_to_string(subtree, prefix + extension, is_last_item))
        
        return '\n'.join(result)
    
    async def execute_operations_async(self):
        """Execute the file operations."""
        if not self.operations:
            self.add_log("✗ No operations to execute")
            return
        
        self.is_processing = True
        self.processing_status = "Executing operations..."
        self.processing_progress = 0
        
        try:
            os.makedirs(self.output_path, exist_ok=True)
            execute_operations(
                self.operations,
                dry_run=False,
                silent=self.silent_mode,
                log_file=None
            )
            self.add_log(f"✓ Successfully organized {len(self.operations)} files!")
            self.processing_status = "Organization complete!"
        except Exception as e:
            self.add_log(f"✗ Error executing operations: {str(e)}")
            self.processing_status = f"Error: {str(e)}"
        finally:
            self.is_processing = False
            self.processing_progress = 100


def header() -> rx.Component:
    """Create the header component."""
    return rx.box(
        rx.hstack(
            rx.heading(
                "🗂️ Local File Organizer",
                size="8",
                weight="bold",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("settings"),
                on_click=State.toggle_settings,
                variant="ghost",
                size="3",
            ),
            width="100%",
            align="center",
        ),
        rx.text(
            "AI-Powered File Organization with Privacy",
            color="gray",
            size="3",
        ),
        padding="1.5em",
        background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        color="white",
        border_radius="0.5em",
        margin_bottom="1em",
    )


def path_configuration() -> rx.Component:
    """Create path configuration section."""
    return rx.card(
        rx.heading("📁 Path Configuration", size="5", margin_bottom="1em"),
        rx.vstack(
            rx.form(
                rx.vstack(
                    rx.text("Input Directory", weight="bold", size="2"),
                    rx.input(
                        placeholder="Enter path to directory you want to organize...",
                        value=State.input_path,
                        on_change=State.set_input_path,
                        width="100%",
                        size="3",
                    ),
                    rx.text("Output Directory", weight="bold", size="2", margin_top="0.5em"),
                    rx.input(
                        placeholder="Enter output path (default: organized_folder)",
                        value=State.output_path,
                        on_change=State.set_output_path,
                        width="100%",
                        size="3",
                    ),
                    rx.hstack(
                        rx.badge(
                            rx.text(f"Files found: {State.file_count}"),
                            color_scheme="blue",
                        ),
                        rx.cond(
                            State.models_initialized,
                            rx.badge("Models Ready", color_scheme="green"),
                            rx.badge("Models Not Initialized", color_scheme="gray"),
                        ),
                        spacing="2",
                        margin_top="0.5em",
                    ),
                    spacing="2",
                    width="100%",
                ),
            ),
            width="100%",
        ),
    )


def mode_selection() -> rx.Component:
    """Create mode selection section."""
    return rx.card(
        rx.heading("🎯 Organization Mode", size="5", margin_bottom="1em"),
        rx.vstack(
            rx.radio_group(
                ["content", "date", "type"],
                value=State.selected_mode,
                on_change=State.set_mode,
                spacing="3",
            ),
            rx.divider(),
            rx.cond(
                State.selected_mode == "content",
                rx.callout(
                    "AI analyzes file content to generate meaningful folder names and filenames",
                    icon="info",
                    color_scheme="blue",
                ),
            ),
            rx.cond(
                State.selected_mode == "date",
                rx.callout(
                    "Organizes files by modification date (year/month)",
                    icon="calendar",
                    color_scheme="green",
                ),
            ),
            rx.cond(
                State.selected_mode == "type",
                rx.callout(
                    "Organizes files by type (images, documents, etc.)",
                    icon="folder",
                    color_scheme="purple",
                ),
            ),
            spacing="3",
            width="100%",
        ),
    )


def preview_section() -> rx.Component:
    """Create preview section."""
    return rx.card(
        rx.heading("👁️ Organization Preview", size="5", margin_bottom="1em"),
        rx.cond(
            State.simulated_tree != "",
            rx.vstack(
                rx.text("Proposed directory structure:", weight="bold", size="2"),
                rx.code_block(
                    State.simulated_tree,
                    width="100%",
                ),
                rx.hstack(
                    rx.button(
                        "Execute Organization",
                        on_click=State.execute_operations_async,
                        color_scheme="green",
                        size="3",
                        disabled=State.is_processing,
                    ),
                    rx.text(State.operations.length(), " operations pending"),
                    spacing="3",
                ),
                spacing="3",
                width="100%",
            ),
            rx.text(
                "Preview will appear here after processing",
                color="gray",
                align="center",
            ),
        ),
    )


def progress_monitor() -> rx.Component:
    """Create progress monitoring section."""
    return rx.card(
        rx.heading("⚡ Progress", size="5", margin_bottom="1em"),
        rx.vstack(
            rx.cond(
                State.is_processing,
                rx.vstack(
                    rx.progress(value=State.processing_progress, width="100%"),
                    rx.text(State.processing_status, size="2", color="gray"),
                    spacing="2",
                    width="100%",
                ),
                rx.text("Ready to process", size="2", color="gray"),
            ),
            rx.button(
                "Start Processing",
                on_click=State.process_files,
                color_scheme="blue",
                size="3",
                width="100%",
                disabled=State.is_processing,
            ),
            spacing="3",
            width="100%",
        ),
    )


def logs_section() -> rx.Component:
    """Create logs section."""
    return rx.card(
        rx.heading("📋 Activity Log", size="5", margin_bottom="1em"),
        rx.box(
            rx.foreach(
                State.log_messages,
                lambda msg: rx.text(msg, font_family="monospace", size="1"),
            ),
            height="200px",
            overflow_y="auto",
            border="1px solid var(--gray-6)",
            border_radius="0.5em",
            padding="1em",
            background="var(--gray-1)",
        ),
    )


def settings_panel() -> rx.Component:
    """Create settings panel."""
    return rx.drawer.root(
        rx.drawer.trigger(rx.box()),
        rx.drawer.overlay(),
        rx.drawer.portal(
            rx.drawer.content(
                rx.vstack(
                    rx.drawer.title("⚙️ Settings"),
                    rx.drawer.description("Configure your preferences"),
                    rx.divider(),
                    rx.vstack(
                        rx.heading("Model Configuration", size="4"),
                        rx.text("Image Model: llava-v1.6-vicuna-7b:q4_0", size="2"),
                        rx.text("Text Model: Llama3.2-3B-Instruct:q3_K_M", size="2"),
                        rx.divider(),
                        rx.heading("Processing Options", size="4"),
                        rx.switch(
                            checked=State.silent_mode,
                            on_change=State.set_silent_mode,
                        ),
                        rx.text("Silent Mode", size="2"),
                        spacing="3",
                        width="100%",
                    ),
                    rx.drawer.close(
                        rx.button("Close", size="3", width="100%"),
                    ),
                    spacing="4",
                    width="100%",
                ),
                padding="2em",
            ),
        ),
        open_=State.show_settings,
    )


def index() -> rx.Component:
    """Main page component."""
    return rx.box(
        header(),
        rx.grid(
            rx.box(
                rx.vstack(
                    path_configuration(),
                    mode_selection(),
                    progress_monitor(),
                    spacing="4",
                ),
            ),
            rx.box(
                rx.vstack(
                    preview_section(),
                    logs_section(),
                    spacing="4",
                ),
            ),
            columns="2",
            spacing="4",
            width="100%",
        ),
        settings_panel(),
        padding="2em",
        max_width="1400px",
        margin="0 auto",
    )


# Create the Reflex app
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="large",
        accent_color="purple",
    ),
)
app.add_page(index, title="Local File Organizer")
