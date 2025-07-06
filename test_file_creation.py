#!/usr/bin/env python3

# Test the file creation functionality
test_response = """
I'll create a profitable automation tool.

**filename: email_automation.py**
```python
import smtplib
from email.mime.text import MIMEText

def send_email(to_email, subject, body):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "your_email@gmail.com"
    password = "your_password"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)

    return "Email sent successfully!"

if __name__ == "__main__":
    send_email("client@example.com", "Test Email", "This is a test email.")
```

This tool can be sold for $29/month to small businesses for email automation.
"""

# Import the file creation function
import sys

sys.path.append(".")
from app import create_file_with_content

# Test the parsing and file creation
if "```python" in test_response and (
    "filename:" in test_response.lower() or "**filename:" in test_response.lower()
):
    try:
        # Extract filename - handle both formats
        lines = test_response.split("\n")
        filename = None
        for line in lines:
            if "filename:" in line.lower():
                # Handle both "filename: file.py" and "**filename: file.py**"
                filename_part = line.split(":")[1].strip()
                filename = filename_part.replace("*", "").strip()
                break

        print(f"Extracted filename: {filename}")

        if filename and filename.endswith(".py"):
            # Extract Python code between ```python and ```
            code_blocks = test_response.split("```python")
            if len(code_blocks) > 1:
                code_part = code_blocks[1]
                code_end = code_part.find("```")
                if code_end > 0:
                    code_content = code_part[:code_end].strip()
                    print(f"Extracted code length: {len(code_content)} characters")
                    print(f"Code preview: {code_content[:100]}...")
                    file_result = create_file_with_content(filename, code_content)
                    print(f"File Creation Result: {file_result}")
                else:
                    print("Warning: Could not find end of code block")
            else:
                print("Warning: Could not find Python code block")
        else:
            print(f"Warning: Invalid or missing filename: {filename}")
    except Exception as e:
        print(f"Error processing file creation: {e}")
else:
    print("No file creation pattern found")
