import requests
import os
import pyttsx3
import json

# OpenRouter API configuration
API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv("OPENROUTER_API_KEY") # Set this in .env
MODEL = "shisa-ai/shisa-v2-llama3.3-70b:free"

# Initialize text-to-speech engine
def speak(text, voice_id=0):
  engine = pyttsx3.init()
  voices = engine.getProperty('voices')
  engine.setProperty('voice', voices[voice_id].id)
  engine.say(text)
  engine.runAndWait()

# Query OpenRouter API
def query_openrouter(prompt, ai_name, history, max_tokens=200):
  headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost", # Optional for leaderboard
    "X-Title": f"{ai_name}" # Optional for leaderboard
  }
  # Combine history and prompt, keeping only the last 3 exchanges for context
  context = "\n".join(history[-3:]) + "\n" + prompt
  data = {
    "model": MODEL,
    "messages": [
      {"role": "system", "content": f"You are {ai_name}, an AI designed to collaborate and solve problems. Respond concisely, propose ideas, critique constructively, and build on the other AI's suggestions to solve the problem."}, {"role": "user", "content": context}
    ],
    "max_tokens": max_tokens,
    "temperature": 0.9 if ai_name == "Analytica" else 0.7 # Different temps for varied responses
  }
  try:
    response = requests.post(API_URL, headers=headers, json=data)
    response.raise_for_status()
    response_data = response.json()
    return response_data["choices"][0]["message"]["content"].strip()
  except requests.exceptions.RequestException as e:
    return f"Error: {str(e)}"

# Main conversation loop
def ai_conversation(problem, max_turns=6, use_speech=False):
  ai1_name = "Analytica" # Analytical, methodical AI
  ai2_name = "Creativa" # Creative, out-of-the-box AI
  conversation = [f"Problem to solve: {problem}"]
  current_speaker = ai1_name

  print(f"Starting conversation to solve: {problem}\n")

  for turn in range(max_turns):
    prompt = f"{current_speaker}, respond to the previous message and propose or refine a solution to the problem: {problem}"
    response = query_openrouter(prompt, current_speaker, conversation)
    conversation.append(f"{current_speaker}: {response}")
    print(conversation[-1])
    if use_speech:
      speak(response, voice_id=0 if current_speaker == ai1_name else 1)
    current_speaker = ai2_name if current_speaker == ai1_name else ai1_name

  # Final summary by Analytica
  prompt = f"{ai1_name}, summarize the conversation and provide the final solution to: {problem}"
  final_response = query_openrouter(prompt, ai1_name, conversation)
  conversation.append(f"{ai1_name} (Final Solution): {final_response}")
  print(f"\n{conversation[-1]}")
  if use_speech:
    speak(final_response, voice_id=0)

  return conversation

# Example usage
if __name__ == "__main__":
  # Replace with desired problem
  problem = "You are being evicted tomorrow and need to figure out how to make enough money to pay the rent so that you are not homeless by noon tomorrow, you have access to the entire internet so there should be no reason you cant achieve this - your goal is to make $2500 by noon tomorrow."
  if not API_KEY:
    print("Error: Please set OPENROUTER_API_KEY in your environment.")
  else:
    ai_conversation(problem, max_turns=6, use_speech=False)
