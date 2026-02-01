"""
Web-based GUI for Local File Organizer using Dash
"""
import os
import time
import threading
from datetime import datetime
from dash import Dash, html, dcc, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

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

from text_data_processing import (
    process_text_files
)

from image_data_processing import (
    process_image_files
)

from output_filter import filter_specific_output

# Lazy imports for Nexa SDK (only when needed)
NexaVLMInference = None
NexaTextInference = None

# Global variables for state management with thread safety
state_lock = threading.Lock()
app_state = {
    'operations': [],
    'image_inference': None,
    'text_inference': None,
    'models_initialized': False,
    'processing': False,
    'log_messages': []
}


def ensure_nltk_data():
    """Ensure that NLTK data is downloaded efficiently and quietly."""
    try:
        import nltk
        nltk.download('stopwords', quiet=True)
        nltk.download('punkt', quiet=True)
        nltk.download('wordnet', quiet=True)
    except Exception as e:
        print(f"Warning: Failed to download NLTK data: {e}")


def initialize_models():
    """Initialize the AI models if not already initialized"""
    global NexaVLMInference, NexaTextInference
    
    if app_state['models_initialized']:
        return True
    
    try:
        # Lazy import Nexa SDK
        if NexaVLMInference is None or NexaTextInference is None:
            try:
                from nexa.gguf import NexaVLMInference as NVLM, NexaTextInference as NTI
                NexaVLMInference = NVLM
                NexaTextInference = NTI
            except ImportError:
                add_log("Error: Nexa SDK not installed. Please install it to use content-based organization.")
                add_log("See README for installation instructions.")
                return False
        
        add_log("Initializing AI models...")
        add_log("Checking if models are already downloaded. If not, downloading now...")
        
        model_path = "llava-v1.6-vicuna-7b:q4_0"
        model_path_text = "Llama3.2-3B-Instruct:q3_K_M"
        
        with filter_specific_output():
            # Initialize the image inference model
            app_state['image_inference'] = NexaVLMInference(
                model_path=model_path,
                local_path=None,
                stop_words=[],
                temperature=0.3,
                max_new_tokens=3000,
                top_k=3,
                top_p=0.2,
                profiling=False
            )
            
            # Initialize the text inference model
            app_state['text_inference'] = NexaTextInference(
                model_path=model_path_text,
                local_path=None,
                stop_words=[],
                temperature=0.5,
                max_new_tokens=3000,
                top_k=3,
                top_p=0.3,
                profiling=False
            )
        
        app_state['models_initialized'] = True
        add_log("✓ Image inference model initialized")
        add_log("✓ Text inference model initialized")
        add_log("-" * 50)
        return True
    except Exception as e:
        add_log(f"Error initializing models: {e}")
        return False


def add_log(message):
    """Add a message to the log (thread-safe)"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    with state_lock:
        app_state['log_messages'].append(f"[{timestamp}] {message}")
        # Keep only last 500 messages
        if len(app_state['log_messages']) > 500:
            app_state['log_messages'] = app_state['log_messages'][-500:]


def get_log_text():
    """Get the current log as text (thread-safe)"""
    with state_lock:
        return "\n".join(app_state['log_messages'])


def simulate_directory_tree(operations, base_path):
    """Simulate the directory tree based on the proposed operations."""
    tree = {}
    for op in operations:
        rel_path = os.path.relpath(op['destination'], base_path)
        parts = rel_path.split(os.sep)
        current_level = tree
        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
    return tree


def format_tree(tree, prefix=''):
    """Format the simulated directory tree as text."""
    lines = []
    pointers = ['├── '] * (len(tree) - 1) + ['└── '] if tree else []
    for pointer, key in zip(pointers, tree):
        lines.append(prefix + pointer + key)
        if tree[key]:
            extension = '│   ' if pointer == '├── ' else '    '
            lines.extend(format_tree(tree[key], prefix + extension))
    return lines


# Initialize Dash app with Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# App layout
app.layout = dbc.Container([
    # Title
    dbc.Row([
        dbc.Col([
            html.H1("Local File Organizer", className="text-center mb-3"),
            html.P("AI-Powered File Management - Privacy Assured", 
                  className="text-center text-muted mb-4")
        ])
    ]),
    
    # Directory Configuration
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Directory Configuration")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Input Directory:"),
                            dbc.Input(id="input-path", type="text", placeholder="/path/to/input/directory"),
                        ], width=12, className="mb-3")
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Output Directory:"),
                            dbc.Input(id="output-path", type="text", 
                                    placeholder="/path/to/output/directory (or leave empty for default)"),
                        ], width=12, className="mb-3")
                    ])
                ])
            ])
        ], width=12, className="mb-3")
    ]),
    
    # Organization Settings
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Organization Settings")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Organize Mode:"),
                            dbc.RadioItems(
                                id="mode-select",
                                options=[
                                    {"label": "By Content (AI)", "value": "content"},
                                    {"label": "By Date", "value": "date"},
                                    {"label": "By Type", "value": "type"}
                                ],
                                value="content",
                                inline=True
                            )
                        ], width=12, className="mb-3")
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Checkbox(id="silent-mode", label="Silent Mode (Log to file)", value=False),
                        ], width=6),
                        dbc.Col([
                            dbc.Checkbox(id="dry-run", label="Dry Run (Preview only)", value=True),
                        ], width=6)
                    ])
                ])
            ])
        ], width=12, className="mb-3")
    ]),
    
    # Action Buttons
    dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("Analyze Files", id="analyze-btn", color="primary", className="me-2"),
                dbc.Button("Organize Files", id="organize-btn", color="success", 
                          className="me-2", disabled=True),
                dbc.Button("Clear Log", id="clear-log-btn", color="secondary")
            ])
        ], className="text-center mb-3")
    ]),
    
    # Progress and Output
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Progress & Output")),
                dbc.CardBody([
                    dbc.Progress(id="progress-bar", value=0, style={"height": "20px"}, 
                               className="mb-3", animated=True, striped=True),
                    html.Div(id="status-text", className="mb-2", 
                            children=html.Strong("Status: Ready", className="text-success")),
                    dcc.Textarea(
                        id="log-output",
                        value="",
                        style={"width": "100%", "height": "400px", "fontFamily": "monospace"},
                        readOnly=True
                    )
                ])
            ])
        ], width=12)
    ]),
    
    # Interval component for updating log
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0),
    
    # Store components for state
    dcc.Store(id='operations-store'),
    dcc.Store(id='processing-store', data=False)
    
], fluid=True, className="p-4")


# Callbacks
@app.callback(
    [Output("log-output", "value"),
     Output("organize-btn", "disabled"),
     Output("status-text", "children"),
     Output("progress-bar", "value")],
    [Input("interval-component", "n_intervals")]
)
def update_log(n):
    """Update the log output periodically"""
    log_text = get_log_text()
    
    # Check if operations are ready (thread-safe)
    with state_lock:
        has_operations = len(app_state['operations']) > 0
        is_processing = app_state['processing']
    
    # Status text
    if is_processing:
        status = html.Strong("Status: Processing...", className="text-warning")
        progress = 50
    elif has_operations:
        status = html.Strong("Status: Ready to organize", className="text-success")
        progress = 0
    else:
        status = html.Strong("Status: Ready", className="text-info")
        progress = 0
    
    return log_text, not has_operations or is_processing, status, progress


@app.callback(
    Output("log-output", "value", allow_duplicate=True),
    [Input("clear-log-btn", "n_clicks")],
    prevent_initial_call=True
)
def clear_log(n_clicks):
    """Clear the log (thread-safe)"""
    if n_clicks:
        with state_lock:
            app_state['log_messages'] = []
        return ""
    return no_update


@app.callback(
    Output("processing-store", "data", allow_duplicate=True),
    [Input("analyze-btn", "n_clicks")],
    [State("input-path", "value"),
     State("output-path", "value"),
     State("mode-select", "value"),
     State("silent-mode", "value")],
    prevent_initial_call=True
)
def analyze_files(n_clicks, input_path, output_path, mode, silent_mode):
    """Analyze files and show preview"""
    if not n_clicks:
        raise PreventUpdate
    
    # Validate inputs
    if not input_path or not os.path.exists(input_path):
        add_log("Error: Please provide a valid input directory")
        return False
    
    # Set default output path
    if not output_path:
        output_path = os.path.join(os.path.dirname(input_path), 'organized_folder')
    
    # Run analysis in a separate thread
    def analyze_thread():
        try:
            with state_lock:
                app_state['processing'] = True
            
            add_log("=" * 50)
            add_log(f"Starting analysis in {mode.upper()} mode")
            add_log("=" * 50)
            
            # Collect file paths
            start_time = time.time()
            file_paths = collect_file_paths(input_path)
            end_time = time.time()
            
            add_log(f"Found {len(file_paths)} files")
            add_log(f"Time taken: {end_time - start_time:.2f} seconds")
            add_log("-" * 50)
            
            # Process based on mode
            if mode == 'content':
                # Initialize models if needed
                if not initialize_models():
                    add_log("Failed to initialize models. Aborting.")
                    with state_lock:
                        app_state['processing'] = False
                    return
                
                add_log("Processing files with AI (this may take a while)...")
                
                # Separate files by type
                image_files, text_files = separate_files_by_type(file_paths)
                add_log(f"Images: {len(image_files)}, Text files: {len(text_files)}")
                
                # Prepare text tuples
                text_tuples = []
                for fp in text_files:
                    text_content = read_file_data(fp)
                    if text_content:
                        text_tuples.append((fp, text_content))
                
                # Process files
                log_file = 'operation_log.txt' if silent_mode else None
                
                with state_lock:
                    img_inf = app_state['image_inference']
                    txt_inf = app_state['text_inference']
                
                data_images = process_image_files(image_files, img_inf, txt_inf,
                                                  silent=silent_mode, log_file=log_file)
                data_texts = process_text_files(text_tuples, txt_inf,
                                               silent=silent_mode, log_file=log_file)
                
                # Combine all data
                all_data = data_images + data_texts
                
                # Compute operations
                renamed_files = set()
                processed_files = set()
                operations = compute_operations(all_data, output_path, 
                                                             renamed_files, processed_files)
                
            elif mode == 'date':
                operations = process_files_by_date(
                    file_paths, output_path, dry_run=False, 
                    silent=silent_mode, 
                    log_file='operation_log.txt' if silent_mode else None
                )
            elif mode == 'type':
                operations = process_files_by_type(
                    file_paths, output_path, dry_run=False, 
                    silent=silent_mode, 
                    log_file='operation_log.txt' if silent_mode else None
                )
            
            # Store operations (thread-safe)
            with state_lock:
                app_state['operations'] = operations
            
            # Show proposed structure
            add_log("-" * 50)
            add_log("Proposed directory structure:")
            add_log(os.path.abspath(output_path))
            simulated_tree = simulate_directory_tree(operations, output_path)
            for line in format_tree(simulated_tree):
                add_log(line)
            add_log("-" * 50)
            add_log(f"Analysis complete! {len(operations)} operations planned.")
            add_log("Click 'Organize Files' to proceed with the changes.")
            
        except Exception as e:
            add_log(f"Error during analysis: {e}")
        finally:
            with state_lock:
                app_state['processing'] = False
    
    thread = threading.Thread(target=analyze_thread)
    thread.daemon = True
    thread.start()
    
    return True


@app.callback(
    Output("processing-store", "data", allow_duplicate=True),
    [Input("organize-btn", "n_clicks")],
    [State("output-path", "value"),
     State("input-path", "value"),
     State("dry-run", "value"),
     State("silent-mode", "value")],
    prevent_initial_call=True
)
def organize_files(n_clicks, output_path, input_path, dry_run, silent_mode):
    """Execute the file organization"""
    if not n_clicks:
        raise PreventUpdate
    
    # Check if operations exist (thread-safe)
    with state_lock:
        has_operations = len(app_state['operations']) > 0
    
    if not has_operations:
        add_log("Error: Please analyze files first")
        return False
    
    # Set default output path
    if not output_path:
        output_path = os.path.join(os.path.dirname(input_path), 'organized_folder')
    
    # Run organization in a separate thread
    def organize_thread():
        try:
            with state_lock:
                app_state['processing'] = True
                operations = app_state['operations'][:]  # Create a copy
            
            # Create output directory
            os.makedirs(output_path, exist_ok=True)
            
            add_log("=" * 50)
            add_log("Performing file operations...")
            add_log("=" * 50)
            
            # Execute operations
            execute_operations(
                operations,
                dry_run=dry_run,
                silent=silent_mode,
                log_file='operation_log.txt' if silent_mode else None
            )
            
            add_log("-" * 50)
            if dry_run:
                add_log("✓ Dry run complete! (No files were actually moved)")
            else:
                add_log("✓ Files organized successfully!")
            add_log("-" * 50)
            
        except Exception as e:
            add_log(f"Error during organization: {e}")
        finally:
            with state_lock:
                app_state['processing'] = False
    
    thread = threading.Thread(target=organize_thread)
    thread.daemon = True
    thread.start()
    
    return True


def main():
    """Main function to run the GUI"""
    ensure_nltk_data()
    
    print("=" * 60)
    print("Local File Organizer - Web Dashboard")
    print("=" * 60)
    print("Starting web server...")
    print("Open your browser and navigate to: http://localhost:8050")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print("NOTE: Server is bound to localhost for security.")
    print("=" * 60)
    
    app.run(debug=False, host='127.0.0.1', port=8050)


if __name__ == '__main__':
    main()
