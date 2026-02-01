import os
import time
import argparse

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

from text_data_processing import (
    process_text_files
)

from image_data_processing import (
    process_image_files
)

from duplicate_checker import (
    find_duplicates,
    handle_duplicates_in_operations
)

from copilot_mode import (
    CopilotMode,
    apply_copilot_rules
)

from organizational_methods import (
    list_methods,
    apply_organizational_method
)

from output_filter import filter_specific_output  # Import the context manager
from nexa.gguf import NexaVLMInference, NexaTextInference  # Import model classes

def ensure_nltk_data():
    """Ensure that NLTK data is downloaded efficiently and quietly."""
    import nltk
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)

# Initialize models
image_inference = None
text_inference = None

def initialize_models(image_model_path=None, text_model_path=None):
    """Initialize the models if they haven't been initialized yet."""
    global image_inference, text_inference
    if image_inference is None or text_inference is None:
        # Initialize the models with default or provided paths
        model_path = image_model_path or "llava-v1.6-vicuna-7b:q4_0"
        model_path_text = text_model_path or "Llama3.2-3B-Instruct:q3_K_M"

        # Use the filter_specific_output context manager
        with filter_specific_output():
            # Initialize the image inference model
            image_inference = NexaVLMInference(
                model_path=model_path,
                local_path=None,
                stop_words=[],
                temperature=0.3,
                max_new_tokens=3000,
                top_k=3,
                top_p=0.2,
                profiling=False
                # add n_ctx if out of context window usage: n_ctx=2048
            )

            # Initialize the text inference model
            text_inference = NexaTextInference(
                model_path=model_path_text,
                local_path=None,
                stop_words=[],
                temperature=0.5,
                max_new_tokens=3000,  # Adjust as needed
                top_k=3,
                top_p=0.3,
                profiling=False
                # add n_ctx if out of context window usage: n_ctx=2048

            )
        print("**----------------------------------------------**")
        print(f"**   Image model: {model_path}")
        print(f"**   Text model: {model_path_text}")
        print("**   Models initialized successfully           **")
        print("**----------------------------------------------**")

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

def print_simulated_tree(tree, prefix=''):
    """Print the simulated directory tree."""
    pointers = ['├── '] * (len(tree) - 1) + ['└── '] if tree else []
    for pointer, key in zip(pointers, tree):
        print(prefix + pointer + key)
        if tree[key]:  # If there are subdirectories or files
            extension = '│   ' if pointer == '├── ' else '    '
            print_simulated_tree(tree[key], prefix + extension)

def get_yes_no(prompt):
    """Prompt the user for a yes/no response."""
    while True:
        response = input(prompt).strip().lower()
        if response in ('yes', 'y'):
            return True
        elif response in ('no', 'n'):
            return False
        elif response == '/exit':
            print("Exiting program.")
            exit()
        else:
            print("Please enter 'yes' or 'no'. To exit, type '/exit'.")

def get_mode_selection():
    """Prompt the user to select a mode."""
    while True:
        print("Please choose the mode to organize your files:")
        print("1. By Content (AI-powered)")
        print("2. By Date")
        print("3. By Type")
        print("4. Copilot Mode (Interactive AI assistant)")
        response = input("Enter 1, 2, 3, or 4 (or type '/exit' to exit): ").strip()
        if response == '/exit':
            print("Exiting program.")
            exit()
        elif response == '1':
            return 'content'
        elif response == '2':
            return 'date'
        elif response == '3':
            return 'type'
        elif response == '4':
            return 'copilot'
        else:
            print("Invalid selection. Please enter 1, 2, 3, or 4. To exit, type '/exit'.")
        else:
            print("Invalid selection. Please enter 1, 2, or 3. To exit, type '/exit'.")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Local File Organizer - AI-powered file organization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py --text-model "Llama3.2-1B-Instruct:q4_0"
  python main.py --image-model "llava-v1.6-vicuna-7b:q4_0" --text-model "Llama3.2-3B-Instruct:q3_K_M"
  python main.py --list-models

Available model examples:
  Text models: Llama3.2-1B-Instruct:q4_0, Llama3.2-3B-Instruct:q3_K_M, gemma-2-2b-instruct:q4_0
  Image models: llava-v1.6-vicuna-7b:q4_0, llava-phi-3-mini:q4_0
        """
    )
    
    parser.add_argument(
        '--text-model',
        type=str,
        default=None,
        help='Text inference model path (default: Llama3.2-3B-Instruct:q3_K_M)'
    )
    
    parser.add_argument(
        '--image-model',
        type=str,
        default=None,
        help='Image inference model path (default: llava-v1.6-vicuna-7b:q4_0)'
    )
    
    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List available model examples and exit'
    )
    
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # If --list-models flag is set, display model info and exit
    if args.list_models:
        print("=" * 60)
        print("Available Model Examples")
        print("=" * 60)
        print("\nText Models (for text analysis and categorization):")
        print("  - Llama3.2-1B-Instruct:q4_0 (smaller, faster)")
        print("  - Llama3.2-3B-Instruct:q3_K_M (default, balanced)")
        print("  - gemma-2-2b-instruct:q4_0 (alternative)")
        print("\nImage Models (for image description and analysis):")
        print("  - llava-v1.6-vicuna-7b:q4_0 (default)")
        print("  - llava-phi-3-mini:q4_0 (smaller, faster)")
        print("\nNote: Models will be downloaded automatically on first use.")
        print("Visit https://nexaai.com for more models.")
        print("=" * 60)
        return
    
    # Ensure NLTK data is downloaded efficiently and quietly
    ensure_nltk_data()

    # Start with dry run set to True
    dry_run = True

    # Display silent mode explanation before asking
    print("-" * 50)
    print("**NOTE: Silent mode logs all outputs to a text file instead of displaying them in the terminal.")
    silent_mode = get_yes_no("Would you like to enable silent mode? (yes/no): ")
    if silent_mode:
        log_file = 'operation_log.txt'
    else:
        log_file = None
    
    # Ask about duplicate checking
    print("-" * 50)
    print("**NOTE: Duplicate checking will detect files with identical content.")
    check_duplicates = get_yes_no("Would you like to check for duplicate files? (yes/no): ")
    if check_duplicates:
        print("How should duplicates be handled?")
        print("1. Keep first occurrence only")
        print("2. Keep all duplicates with unique names")
        print("3. Skip all duplicates")
        while True:
            dup_choice = input("Enter 1, 2, or 3: ").strip()
            if dup_choice == '1':
                duplicate_strategy = 'keep_first'
                break
            elif dup_choice == '2':
                duplicate_strategy = 'keep_all'
                break
            elif dup_choice == '3':
                duplicate_strategy = 'skip_duplicates'
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    else:
        duplicate_strategy = None
    
    # Ask about organizational methodology
    print("-" * 50)
    print("**NOTE: You can apply organizational best practices to your file structure.")
    use_org_method = get_yes_no("Would you like to use an organizational methodology? (yes/no): ")
    if use_org_method:
        print("\nAvailable organizational methods:")
        methods = list_methods()
        for i, method in enumerate(methods, 1):
            print(f"{i}. {method['name']}: {method['description']}")
        
        while True:
            org_choice = input(f"Enter 1-{len(methods)} (or 'skip' to proceed without): ").strip()
            if org_choice.lower() == 'skip':
                organizational_method = None
                break
            try:
                choice_idx = int(org_choice) - 1
                if 0 <= choice_idx < len(methods):
                    organizational_method = methods[choice_idx]['key']
                    print(f"Selected: {methods[choice_idx]['name']}")
                    break
                else:
                    print(f"Invalid choice. Please enter 1-{len(methods)} or 'skip'.")
            except ValueError:
                print(f"Invalid input. Please enter 1-{len(methods)} or 'skip'.")
    else:
        organizational_method = None

    while True:
        # Paths configuration
        if not silent_mode:
            print("-" * 50)

        # Get input and output paths once per directory
        input_path = input("Enter the path of the directory you want to organize: ").strip()
        while not os.path.exists(input_path):
            message = f"Input path {input_path} does not exist. Please enter a valid path."
            if silent_mode:
                with open(log_file, 'a') as f:
                    f.write(message + '\n')
            else:
                print(message)
            input_path = input("Enter the path of the directory you want to organize: ").strip()

        # Confirm successful input path
        message = f"Input path successfully uploaded: {input_path}"
        if silent_mode:
            with open(log_file, 'a') as f:
                f.write(message + '\n')
        else:
            print(message)
        if not silent_mode:
            print("-" * 50)

        # Default output path is a folder named "organized_folder" in the same directory as the input path
        output_path = input("Enter the path to store organized files and folders (press Enter to use 'organized_folder' in the input directory): ").strip()
        if not output_path:
            # Get the parent directory of the input path and append 'organized_folder'
            output_path = os.path.join(os.path.dirname(input_path), 'organized_folder')

        # Confirm successful output path
        message = f"Output path successfully set to: {output_path}"
        if silent_mode:
            with open(log_file, 'a') as f:
                f.write(message + '\n')
        else:
            print(message)
        if not silent_mode:
            print("-" * 50)

        # Start processing files
        start_time = time.time()
        file_paths = collect_file_paths(input_path)
        end_time = time.time()

        message = f"Time taken to load file paths: {end_time - start_time:.2f} seconds"
        if silent_mode:
            with open(log_file, 'a') as f:
                f.write(message + '\n')
        else:
            print(message)
        if not silent_mode:
            print("-" * 50)
            print("Directory tree before organizing:")
            display_directory_tree(input_path)

            print("*" * 50)

        # Loop for selecting sorting methods
        while True:
            mode = get_mode_selection()

            if mode == 'content':
                # Proceed with content mode
                # Initialize models once
                if not silent_mode:
                    print("Checking if the model is already downloaded. If not, downloading it now.")
                initialize_models(image_model_path=args.image_model, text_model_path=args.text_model)

                if not silent_mode:
                    print("*" * 50)
                    print("The file upload was successful. Processing may take a few minutes.")
                    print("*" * 50)

                # Prepare to collect link type statistics
                link_type_counts = {'hardlink': 0, 'symlink': 0}

                # Separate files by type
                image_files, text_files, audio_files, video_files = separate_files_by_type(file_paths)
                
                # Note about audio/video files in content mode
                if (audio_files or video_files) and not silent_mode:
                    print("*" * 50)
                    print("Note: Audio and video files will be organized by type/date only.")
                    print("Content-based organization is not available for multimedia files.")
                    print("*" * 50)

                # Prepare text tuples for processing
                text_tuples = []
                for fp in text_files:
                    # Use read_file_data to read the file content
                    text_content = read_file_data(fp)
                    if text_content is None:
                        message = f"Unsupported or unreadable text file format: {fp}"
                        if silent_mode:
                            with open(log_file, 'a') as f:
                                f.write(message + '\n')
                        else:
                            print(message)
                        continue  # Skip unsupported or unreadable files
                    text_tuples.append((fp, text_content))

                # Process files sequentially
                data_images = process_image_files(image_files, image_inference, text_inference, silent=silent_mode, log_file=log_file)
                data_texts = process_text_files(text_tuples, text_inference, silent=silent_mode, log_file=log_file)

                # Prepare for copying and renaming
                renamed_files = set()
                processed_files = set()

                # Combine all data
                all_data = data_images + data_texts

                # Compute the operations
                operations = compute_operations(
                    all_data,
                    output_path,
                    renamed_files,
                    processed_files
                )

            elif mode == 'date':
                # Process files by date
                operations = process_files_by_date(file_paths, output_path, dry_run=False, silent=silent_mode, log_file=log_file)
            elif mode == 'type':
                # Process files by type
                operations = process_files_by_type(file_paths, output_path, dry_run=False, silent=silent_mode, log_file=log_file)
            elif mode == 'copilot':
                # Copilot mode - interactive AI assistant
                # Initialize models for copilot mode
                if not silent_mode:
                    print("Initializing AI for copilot mode...")
                initialize_models(image_model_path=args.image_model, text_model_path=args.text_model)
                
                # Create copilot instance
                copilot = CopilotMode(text_inference, silent=silent_mode, log_file=log_file)
                
                # Run interactive session
                custom_instructions = copilot.run_interactive_session(file_paths)
                
                if custom_instructions is None:
                    # User exited copilot mode
                    print("Copilot mode canceled.")
                    continue  # Go back to mode selection
                
                # Apply custom rules
                operations = apply_copilot_rules(custom_instructions, output_path)
            else:
                print("Invalid mode selected.")
                return

            # Handle duplicate checking if enabled
            if check_duplicates and duplicate_strategy:
                if not silent_mode:
                    print("-" * 50)
                    print("Checking for duplicate files...")
                
                # Find duplicates among source files
                source_files = [op['source'] for op in operations]
                duplicates = find_duplicates(source_files, silent=silent_mode, log_file=log_file)
                
                # Apply duplicate handling strategy
                if duplicates:
                    operations = handle_duplicates_in_operations(
                        operations, 
                        duplicate_strategy=duplicate_strategy,
                        silent=silent_mode,
                        log_file=log_file
                    )
            
            # Apply organizational methodology if selected
            if organizational_method and mode not in ['copilot']:
                if not silent_mode:
                    print("-" * 50)
                    print(f"Applying {organizational_method} organizational methodology...")
                
                # Extract source files and create metadata dict if available
                source_files = [op['source'] for op in operations]
                metadata_dict = {}
                
                # For content mode, we have metadata
                if mode == 'content':
                    for data in all_data:
                        metadata_dict[data['file_path']] = {
                            'foldername': data['foldername'],
                            'filename': data['filename']
                        }
                
                # Recompute operations with organizational method
                operations = apply_organizational_method(
                    source_files,
                    output_path,
                    organizational_method,
                    metadata_dict=metadata_dict if metadata_dict else None
                )

            # Simulate and display the proposed directory tree
            print("-" * 50)
            message = "Proposed directory structure:"
            if silent_mode:
                with open(log_file, 'a') as f:
                    f.write(message + '\n')
            else:
                print(message)
                print(os.path.abspath(output_path))
                simulated_tree = simulate_directory_tree(operations, output_path)
                print_simulated_tree(simulated_tree)
                print("-" * 50)

            # Ask user if they want to proceed
            proceed = get_yes_no("Would you like to proceed with these changes? (yes/no): ")
            if proceed:
                # Create the output directory now
                os.makedirs(output_path, exist_ok=True)

                # Perform the actual file operations
                message = "Performing file operations..."
                if silent_mode:
                    with open(log_file, 'a') as f:
                        f.write(message + '\n')
                else:
                    print(message)
                execute_operations(
                    operations,
                    dry_run=False,
                    silent=silent_mode,
                    log_file=log_file
                )

                message = "The files have been organized successfully."
                if silent_mode:
                    with open(log_file, 'a') as f:
                        f.write("-" * 50 + '\n' + message + '\n' + "-" * 50 + '\n')
                else:
                    print("-" * 50)
                    print(message)
                    print("-" * 50)
                break  # Exit the sorting method loop after successful operation
            else:
                # Ask if the user wants to try another sorting method
                another_sort = get_yes_no("Would you like to choose another sorting method? (yes/no): ")
                if another_sort:
                    continue  # Loop back to mode selection
                else:
                    print("Operation canceled by the user.")
                    break  # Exit the sorting method loop

        # Ask if the user wants to organize another directory
        another_directory = get_yes_no("Would you like to organize another directory? (yes/no): ")
        if not another_directory:
            break  # Exit the main loop


if __name__ == '__main__':
    main()
