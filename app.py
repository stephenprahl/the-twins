import requests
import os
import subprocess
import shutil
import json
import time

# OpenRouter API configuration
API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv("OPENROUTER_API_KEY")  # Set in .env or environment
MODEL = "deepseek/deepseek-r1:free"

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


# Query OpenRouter API
def query_openrouter(prompt, ai_name, history, max_tokens=200):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": f"{ai_name}",
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
        "max_tokens": max_tokens,
        "temperature": 0.9 if ai_name == "Analytica" else 0.7,
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as e:
        if "429" in str(e):
            print("Rate limit hit, waiting 60 seconds...")
            time.sleep(60)
            return "I need to wait a moment due to rate limits. Let me continue in a moment."
        return f"HTTP Error: {str(e)}"
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
        response = query_openrouter(prompt, current_speaker, conversation)

        # Handle API errors gracefully
        if "Error:" in response:
            print(f"API Error encountered: {response}")
            if "rate limit" in response.lower():
                time.sleep(60)  # Wait for rate limit reset
                continue
            else:
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

        # Add a small delay to respect rate limits
        time.sleep(2)

    # Final summary by Analytica
    prompt = f"{ai1_name}, provide a comprehensive business summary including: 1) All products created, 2) Revenue projections and pricing strategy, 3) Marketing/distribution plan, 4) Next steps for monetization. Final solution for: {problem}"
    final_response = query_openrouter(prompt, ai1_name, conversation)
    conversation.append(f"{ai1_name} (Final Solution): {final_response}")
    print(f"\n{conversation[-1]}")

    return conversation


# Example usage
if __name__ == "__main__":
    # High-probability money-making focus
    problem = "Create and package profitable Python tools or automation scripts that can be sold online for recurring revenue. Target high-demand niches like productivity automation, data processing, or business tools. Include pricing strategy and distribution plan."
    if not API_KEY:
        print("Error: Please set OPENROUTER_API_KEY in your environment.")
    else:
        ai_conversation(problem, max_turns=None, use_speech=False)
