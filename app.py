import requests
import os
import subprocess
import shutil
import json
import time

# Ollama API configuration
API_URL = "http://localhost:11434/api/chat"
MODEL = "deepseek-r1:1.5b"  # Fast, efficient model for collaboration

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
    "pip",
    "git",
    "curl",
    "wget",
    "chmod",
    "cp",
    "mv",
]
ALLOWED_DIRS = [os.path.expanduser("~/ai_tasks")]  # Restrict to a specific directory
OUTPUT_DIR = ALLOWED_DIRS[0]

# Initialize output directory
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


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
                "content": f"You are {ai_name}, an AI entrepreneur focused on creating profitable digital products. Your goal is to collaborate and build marketable Python tools, automation scripts, or SaaS prototypes that can generate revenue quickly. Focus on: 1) High-demand niches (productivity, automation, data tools), 2) Quick-to-build solutions, 3) Scalable products. Propose commands within the whitelist {ALLOWED_COMMANDS}, restricted to {ALLOWED_DIRS}. Always include market research, pricing strategy, and distribution plans. Respond concisely and build on the other AI's suggestions.",
            },
            {"role": "user", "content": context},
        ],
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.9 if ai_name == "Analytica" else 0.7,
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
        prompt = f"{current_speaker}, respond to the previous message and propose a specific task to build a profitable digital product for: {problem}. Focus on quick wins with high revenue potential. Include market size, pricing, and distribution strategy. Specify if the task is destructive. Include the command in a code block (```bash\ncommand\n```). If you believe the solution is complete and ready for monetization, say 'SOLUTION_COMPLETE' at the end of your response."
        response = query_ollama(prompt, current_speaker, conversation)

        # Handle API errors gracefully
        if "Error:" in response:
            print(f"API Error encountered: {response}")
            print("Continuing despite error...")

        conversation.append(f"{current_speaker}: {response}")
        print(conversation[-1])

        # Check for command in response
        if "```bash" in response:
            command = response.split("```bash\n")[1].split("```")[0].strip()
            is_destructive = "destructive" in response.lower()
            command_result = execute_command(command, is_destructive)
            conversation.append(f"Command Result: {command_result}")
            print(f"Command Result: {command_result}")

        # Check if solution is complete
        if "SOLUTION_COMPLETE" in response:
            print(
                f"\n{current_speaker} indicates the solution is complete. Moving to final summary...\n"
            )
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
