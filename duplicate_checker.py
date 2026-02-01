"""
Duplicate file detection and management utilities.
"""

import os
import hashlib
from collections import defaultdict


def calculate_file_hash(file_path, algorithm='sha256', chunk_size=8192):
    """
    Calculate the hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use ('md5' or 'sha256')
        chunk_size: Size of chunks to read at a time
        
    Returns:
        Hex digest of the file hash
    """
    if algorithm == 'md5':
        hasher = hashlib.md5()
    elif algorithm == 'sha256':
        hasher = hashlib.sha256()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {e}")
        return None


def find_duplicates(file_paths, algorithm='sha256', silent=False, log_file=None):
    """
    Find duplicate files based on their content hash.
    
    Args:
        file_paths: List of file paths to check
        algorithm: Hash algorithm to use ('md5' or 'sha256')
        silent: Whether to suppress output
        log_file: Path to log file for silent mode
        
    Returns:
        Dictionary mapping hash to list of duplicate file paths
    """
    hash_to_files = defaultdict(list)
    
    message = f"Calculating file hashes to detect duplicates..."
    if silent:
        if log_file:
            with open(log_file, 'a') as f:
                f.write(message + '\n')
    else:
        print(message)
    
    for file_path in file_paths:
        file_hash = calculate_file_hash(file_path, algorithm)
        if file_hash:
            hash_to_files[file_hash].append(file_path)
    
    # Filter to only keep hashes with multiple files (duplicates)
    duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
    
    if duplicates:
        message = f"\nFound {len(duplicates)} sets of duplicate files:"
        if silent:
            if log_file:
                with open(log_file, 'a') as f:
                    f.write(message + '\n')
        else:
            print(message)
            
        for file_hash, files in duplicates.items():
            message = f"\nDuplicate set (hash: {file_hash[:16]}...):"
            if silent:
                if log_file:
                    with open(log_file, 'a') as f:
                        f.write(message + '\n')
            else:
                print(message)
                
            for file_path in files:
                message = f"  - {file_path}"
                if silent:
                    if log_file:
                        with open(log_file, 'a') as f:
                            f.write(message + '\n')
                else:
                    print(message)
    else:
        message = "\nNo duplicate files found."
        if silent:
            if log_file:
                with open(log_file, 'a') as f:
                    f.write(message + '\n')
        else:
            print(message)
    
    return duplicates


def handle_duplicates_in_operations(operations, duplicate_strategy='keep_first', silent=False, log_file=None):
    """
    Handle duplicate files in operations based on the chosen strategy.
    
    Args:
        operations: List of file operations
        duplicate_strategy: How to handle duplicates ('keep_first', 'keep_all', 'skip_duplicates')
        silent: Whether to suppress output
        log_file: Path to log file for silent mode
        
    Returns:
        Filtered list of operations based on duplicate strategy
    """
    if duplicate_strategy == 'keep_all':
        # Keep all files, just rename duplicates with unique suffixes
        return operations
    
    # Build hash map of source files
    source_hashes = {}
    for op in operations:
        file_hash = calculate_file_hash(op['source'])
        if file_hash:
            if file_hash not in source_hashes:
                source_hashes[file_hash] = []
            source_hashes[file_hash].append(op)
    
    filtered_operations = []
    
    if duplicate_strategy == 'keep_first':
        # Keep only the first occurrence of each unique file
        for file_hash, ops in source_hashes.items():
            if len(ops) > 1:
                message = f"\nSkipping {len(ops) - 1} duplicate(s) of: {os.path.basename(ops[0]['source'])}"
                if silent:
                    if log_file:
                        with open(log_file, 'a') as f:
                            f.write(message + '\n')
                else:
                    print(message)
            filtered_operations.append(ops[0])
    
    elif duplicate_strategy == 'skip_duplicates':
        # Skip all duplicates, only keep unique files
        for file_hash, ops in source_hashes.items():
            if len(ops) == 1:
                filtered_operations.append(ops[0])
            else:
                message = f"\nSkipping all {len(ops)} instances of duplicate file: {os.path.basename(ops[0]['source'])}"
                if silent:
                    if log_file:
                        with open(log_file, 'a') as f:
                            f.write(message + '\n')
                else:
                    print(message)
    
    return filtered_operations
