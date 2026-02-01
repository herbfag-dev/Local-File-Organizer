"""
Copilot Mode - Interactive AI-powered file organization assistant.
"""

import os
from nexa.gguf import NexaTextInference


class CopilotMode:
    """Interactive copilot mode for custom file organization."""
    
    def __init__(self, text_inference, silent=False, log_file=None):
        """
        Initialize copilot mode.
        
        Args:
            text_inference: NexaTextInference instance
            silent: Whether to suppress output
            log_file: Path to log file for silent mode
        """
        self.text_inference = text_inference
        self.silent = silent
        self.log_file = log_file
        self.conversation_history = []
    
    def print_message(self, message):
        """Print message based on silent mode setting."""
        if self.silent:
            if self.log_file:
                with open(self.log_file, 'a') as f:
                    f.write(message + '\n')
        else:
            print(message)
    
    def get_user_input(self, prompt):
        """Get input from user."""
        if self.silent:
            return ""
        return input(prompt).strip()
    
    def run_interactive_session(self, file_paths):
        """
        Run an interactive copilot session.
        
        Args:
            file_paths: List of file paths to potentially organize
            
        Returns:
            Dictionary with custom organization instructions or None
        """
        self.print_message("\n" + "=" * 60)
        self.print_message("Welcome to Copilot Mode!")
        self.print_message("=" * 60)
        self.print_message("\nIn this mode, you can chat with AI to define custom")
        self.print_message("file organization rules. For example:")
        self.print_message("  - 'Rename all PDFs to include their creation date'")
        self.print_message("  - 'Organize images by the year they were taken'")
        self.print_message("  - 'Group all work-related files into a Work folder'")
        self.print_message("\nType '/exit' to leave copilot mode")
        self.print_message("Type '/files' to see a list of files")
        self.print_message("Type '/apply' when ready to apply your rules")
        self.print_message("=" * 60 + "\n")
        
        # Initialize conversation with file context
        file_summary = self._create_file_summary(file_paths)
        system_context = f"""You are a helpful AI assistant for file organization.
The user has {len(file_paths)} files to organize.

File summary:
{file_summary}

Help the user define clear organization rules. Be concise and practical."""
        
        self.conversation_history.append({
            "role": "system",
            "content": system_context
        })
        
        custom_rules = []
        
        while True:
            user_message = self.get_user_input("\nYou: ")
            
            if user_message.lower() == '/exit':
                self.print_message("\nExiting copilot mode.")
                return None
            
            elif user_message.lower() == '/files':
                self._show_files(file_paths)
                continue
            
            elif user_message.lower() == '/apply':
                if custom_rules:
                    self.print_message("\n" + "=" * 60)
                    self.print_message("Custom Rules Summary:")
                    for i, rule in enumerate(custom_rules, 1):
                        self.print_message(f"{i}. {rule}")
                    self.print_message("=" * 60)
                    
                    confirm = self.get_user_input("\nApply these rules? (yes/no): ")
                    if confirm.lower() in ('yes', 'y'):
                        return {'rules': custom_rules, 'file_paths': file_paths}
                    else:
                        self.print_message("Rules not applied. Continue defining rules or type '/exit'.")
                        continue
                else:
                    self.print_message("No rules defined yet. Continue chatting to define rules.")
                    continue
            
            elif not user_message:
                continue
            
            # Add user message to conversation
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Generate AI response
            ai_response = self._get_ai_response()
            
            self.print_message(f"\nAI: {ai_response}")
            
            # Check if AI suggested a rule
            if "rule:" in ai_response.lower() or "organize" in ai_response.lower():
                extract_rule = self.get_user_input("\nWould you like to add this as a rule? (yes/no): ")
                if extract_rule.lower() in ('yes', 'y'):
                    rule_description = self.get_user_input("Describe the rule briefly: ")
                    if rule_description:
                        custom_rules.append(rule_description)
                        self.print_message(f"✓ Rule added: {rule_description}")
    
    def _create_file_summary(self, file_paths):
        """Create a summary of files to organize."""
        from collections import Counter
        
        # Count file types
        extensions = [os.path.splitext(fp)[1].lower() for fp in file_paths]
        ext_counts = Counter(extensions)
        
        summary = []
        summary.append(f"Total files: {len(file_paths)}")
        summary.append("\nFile types:")
        for ext, count in ext_counts.most_common(10):
            ext_name = ext if ext else "(no extension)"
            summary.append(f"  {ext_name}: {count} file(s)")
        
        if len(ext_counts) > 10:
            summary.append(f"  ... and {len(ext_counts) - 10} more types")
        
        return "\n".join(summary)
    
    def _show_files(self, file_paths):
        """Display list of files."""
        self.print_message("\n" + "=" * 60)
        self.print_message("Files to organize:")
        self.print_message("=" * 60)
        
        max_display = 20
        for i, fp in enumerate(file_paths[:max_display], 1):
            self.print_message(f"{i}. {os.path.basename(fp)} ({os.path.splitext(fp)[1]})")
        
        if len(file_paths) > max_display:
            self.print_message(f"... and {len(file_paths) - max_display} more files")
        
        self.print_message("=" * 60)
    
    def _get_ai_response(self):
        """Get AI response based on conversation history."""
        # Build prompt from conversation history
        prompt = ""
        for msg in self.conversation_history[1:]:  # Skip system message
            if msg["role"] == "user":
                prompt += f"User: {msg['content']}\n"
            else:
                prompt += f"Assistant: {msg['content']}\n"
        
        prompt += "Assistant:"
        
        try:
            response = self.text_inference.create_completion(prompt, max_tokens=300)
            ai_text = response['choices'][0]['text'].strip()
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_text
            })
            
            return ai_text
        except Exception as e:
            error_msg = f"Error getting AI response: {e}"
            self.print_message(error_msg)
            return "I apologize, but I encountered an error. Please try rephrasing your request."


def apply_copilot_rules(custom_instructions, output_path):
    """
    Apply custom rules from copilot mode to generate file operations.
    
    Args:
        custom_instructions: Dictionary with rules and file_paths
        output_path: Output directory path
        
    Returns:
        List of file operations
    """
    # For now, this is a simplified implementation
    # In a full implementation, this would parse the rules and create operations
    operations = []
    
    rules = custom_instructions.get('rules', [])
    file_paths = custom_instructions.get('file_paths', [])
    
    # Create a basic organization based on file types
    # This is a placeholder - a full implementation would parse and execute the actual rules
    for file_path in file_paths:
        ext = os.path.splitext(file_path)[1].lower()
        
        # Simple categorization
        if ext in ['.txt', '.doc', '.docx', '.pdf']:
            folder = 'Documents'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
            folder = 'Images'
        elif ext in ['.mp3', '.wav', '.flac']:
            folder = 'Audio'
        elif ext in ['.mp4', '.avi', '.mkv']:
            folder = 'Video'
        else:
            folder = 'Other'
        
        new_path = os.path.join(output_path, folder, os.path.basename(file_path))
        
        operations.append({
            'source': file_path,
            'destination': new_path,
            'link_type': 'hardlink'
        })
    
    return operations
