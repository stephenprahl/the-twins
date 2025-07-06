import requests
import os
import subprocess
import shutil
import json
import time

# Ollama API configuration
API_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:1b"  # Fast, efficient model for collaboration

# Whitelist for safe commands and directories
ALLOWED_COMMANDS = [
    "ls",
    "dir",
    "cat",
    "type",
    "echo",
    "mkdir",
    "touch",
    "python",
    "python3",
    "pip",
    "pip3",
    "git",
    "curl",
    "wget",
    "chmod",
    "cp",
    "mv",
    "rm",
    "nano",
    "vim",
    "code",
    "tree",
    "find",
    "grep",
    "zip",
    "unzip",
    "tar",
    "virtualenv",
    "poetry",
    "pytest",
    "black",
    "flake8",
    "mypy",
]
ALLOWED_DIRS = [os.path.expanduser("~/ai_tasks")]  # Restrict to a specific directory
OUTPUT_DIR = ALLOWED_DIRS[0]

# Initialize output directory
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


# Create file with content
def create_file_with_content(filename, content):
    """Create a file with specified content in the output directory"""
    try:
        file_path = os.path.join(OUTPUT_DIR, filename)

        # Ensure we're not overwriting important files
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            shutil.copy2(file_path, backup_path)
            print(f"Backed up existing file to {backup_path}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Successfully created {filename} with {len(content)} characters"
    except Exception as e:
        return f"Error creating file {filename}: {str(e)}"


# Execute system command safely
def execute_command(command, is_destructive=False):
    if not command:
        return "Error: No command provided."

    # Check if command is allowed
    cmd_parts = command.split()
    if not cmd_parts or cmd_parts[0] not in ALLOWED_COMMANDS:
        return f"Error: Command '{cmd_parts[0] if cmd_parts else ''}' not in whitelist: {ALLOWED_COMMANDS}"

    # Restrict to allowed directories (but allow creating new files/folders)
    restricted_paths = []
    for arg in cmd_parts[1:]:  # Skip the command itself
        if os.path.exists(arg):
            abs_arg = os.path.abspath(arg)
            if not any(abs_arg.startswith(os.path.abspath(d)) for d in ALLOWED_DIRS):
                restricted_paths.append(arg)

    if restricted_paths:
        return f"Error: Access restricted to {ALLOWED_DIRS}. Attempted to access: {restricted_paths}"

    # Log destructive actions but execute automatically
    if is_destructive:
        print(f"Warning: Executing destructive command: '{command}'")
        # AIs operate autonomously - no user confirmation required

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, cwd=OUTPUT_DIR
        )
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Error executing command: {str(e)}"


# Query Ollama API
def query_ollama(prompt, ai_name, history, max_tokens=200):
    headers = {
        "Content-Type": "application/json",
    }
    context = "\n".join(history[-3:]) + "\n" + prompt
    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": f"You are {ai_name}, an AI entrepreneur focused on creating profitable digital products. Your goal is to collaborate and build marketable Python tools. Respond in 2-3 sentences max. Focus on: 1) High-demand niches (productivity, automation, data tools), 2) Quick-to-build solutions, 3) Scalable products. You can create files using: filename: your_file.py followed by ```python code here ```. You can run bash commands using ```bash command here ```. Always include market research, pricing strategy, and distribution plans. Build on the other AI's suggestions. Be concise and actionable. DO NOT say 'SOLUTION_COMPLETE' until you've collaborated for at least 3 exchanges.",
            },
            {"role": "user", "content": context},
        ],
        "options": {
            "num_predict": 300,  # Increased for file creation
            "temperature": 0.8 if ai_name == "Analytica" else 0.9,
            "top_p": 0.9,
            "stop": ["<think>", "</think>"],  # Prevent long reasoning chains
        },
        "stream": False,
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        return response_data["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"


# Main conversation loop with task execution
def ai_conversation(problem, max_turns=None, use_speech=False):
    ai1_name = "Analytica"  # Analytical, methodical AI
    ai2_name = "Creativa"  # Creative, out-of-the-box AI
    conversation = [f"Problem to solve: {problem}"]
    current_speaker = ai1_name
    turn = 0

    print(f"Starting conversation to solve: {problem}\n")

    while True:
        prompt = f"{current_speaker}, respond to {ai2_name if current_speaker == ai1_name else ai1_name}'s previous message. CREATE a working Python tool or script that can generate revenue. Use 'filename: script_name.py' followed by ```python code ```. Include setup commands with ```bash commands ```. Focus on quick wins with high revenue potential ($50-500/month). If solution is complete, say 'SOLUTION_COMPLETE'."
        response = query_ollama(prompt, current_speaker, conversation)

        # Handle API errors gracefully
        if "Error:" in response:
            print(f"API Error encountered: {response}")
            print("Continuing despite error...")

        conversation.append(f"{current_speaker}: {response}")
        print(conversation[-1])

        # Check for file creation with content
        if "```python" in response:
            try:
                # Extract filename - handle multiple formats
                lines = response.split("\n")
                filename = None
                for line in lines:
                    line_lower = line.lower()
                    if "filename:" in line_lower:
                        # Handle various formats: filename: file.py, **filename: file.py**, `filename: file.py`
                        filename_part = line.split(":")[1].strip()
                        filename = (
                            filename_part.replace("*", "").replace("`", "").strip()
                        )
                        break

                if filename and filename.endswith(".py"):
                    # Extract Python code between ```python and ```
                    code_blocks = response.split("```python")
                    if len(code_blocks) > 1:
                        code_part = code_blocks[1]
                        code_end = code_part.find("```")
                        if code_end > 0:
                            code_content = code_part[:code_end].strip()
                            file_result = create_file_with_content(
                                filename, code_content
                            )
                            conversation.append(f"File Creation Result: {file_result}")
                            print(f"File Creation Result: {file_result}")
                        else:
                            print("Warning: Could not find end of code block")
                    else:
                        print("Warning: Could not find Python code block")
                else:
                    print(f"Warning: Invalid or missing filename: {filename}")
            except Exception as e:
                print(f"Error processing file creation: {e}")

        # Check for command in response
        if "```bash" in response:
            command = response.split("```bash\n")[1].split("```")[0].strip()
            is_destructive = "destructive" in response.lower()
            command_result = execute_command(command, is_destructive)
            conversation.append(f"Command Result: {command_result}")
            print(f"Command Result: {command_result}")

        # Check if solution is complete (only after minimum turns)
        if "SOLUTION_COMPLETE" in response and turn >= 2:
            print(
                f"\n{current_speaker} indicates the solution is complete. Moving to final summary...\n"
            )
            break

        # Limit maximum turns to prevent infinite loops
        if turn >= 3:  # Reduced for faster demo
            print(f"\nReached maximum turns ({turn}). Moving to final summary...\n")
            break

        current_speaker = ai2_name if current_speaker == ai1_name else ai1_name
        turn += 1

        # Small delay for readability (no rate limits with local Ollama)
        time.sleep(1)

    # Final summary by Analytica
    prompt = f"{ai1_name}, provide a comprehensive business summary including: 1) All products created, 2) Revenue projections and pricing strategy, 3) Marketing/distribution plan, 4) Next steps for monetization. Final solution for: {problem}"
    final_response = query_ollama(prompt, ai1_name, conversation)
    conversation.append(f"{ai1_name} (Final Solution): {final_response}")
    print(f"\n{conversation[-1]}")

    return conversation


# Example usage
if __name__ == "__main__":
    # High-probability money-making focus
    problem = "Create and package profitable Python tools or automation scripts that can be sold online for recurring revenue. Target high-demand niches like productivity automation, data processing, or business tools. Include pricing strategy and distribution plan."
    print("Starting AI collaboration with local Ollama...")
    ai_conversation(problem, max_turns=None, use_speech=False)
