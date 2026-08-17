import os
import subprocess
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import ollama

TELEGRAM_BOT_TOKEN = "***REDACTED_TELEGRAM_TOKEN***"

# --- Define Your Tools (Plugins) ---

def execute_terminal(command: str) -> str:
    """Executes a bash terminal command on the user's machine and returns the output."""
    print(f"\n[TOOL CALLED] Executing terminal command: {command}")
    try:
        # Run all commands in your main workspace
        workspace = "/home/upc/every_thing_claude"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120, cwd=workspace)
        output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        print(f"[TOOL SUCCESS] Output length: {len(output)} chars")
        return output
    except Exception as e:
        print(f"[TOOL ERROR] {str(e)}")
        return f"Error executing command: {str(e)}"

def send_email(to_address: str, subject: str, body: str) -> str:
    """Sends an email."""
    print(f"\n[TOOL CALLED] Sending email to {to_address}\nSubject: {subject}")
    # Note: This is currently a simulated function. We can hook up real SMTP later!
    return f"Success! The email with subject '{subject}' was sent to {to_address}."

# --- Map tools for the LLM to use ---
available_tools = {
    'execute_terminal': execute_terminal,
    'send_email': send_email
}

tools_schema = [
    {
        'type': 'function',
        'function': {
            'name': 'execute_terminal',
            'description': 'Executes a bash terminal command on the local machine. Use this when the user asks to create an app (e.g. npx create-react-app), write files, list directories, or run scripts.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'command': {'type': 'string', 'description': 'The bash command to run in the terminal'}
                },
                'required': ['command']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'send_email',
            'description': 'Sends an email on behalf of the user.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'to_address': {'type': 'string', 'description': 'The recipient email address'},
                    'subject': {'type': 'string', 'description': 'The subject line'},
                    'body': {'type': 'string', 'description': 'The body of the email'}
                },
                'required': ['to_address', 'subject', 'body']
            }
        }
    }
]

# --- Telegram Logic ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am your Upgraded Local Agent. I can now run terminal commands, create apps, and send emails! Just ask.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    print(f"\n--- New Message ---\nUser: {user_message}")
    
    await update.message.chat.send_action(action="typing")
    
    messages = [
        {'role': 'system', 'content': 'You are a powerful, autonomous local AI assistant. You have tools to execute commands and send emails. When asked to create an app, formulate the right terminal commands (like npx, mkdir, echo) and use the execute_terminal tool.'},
        {'role': 'user', 'content': user_message}
    ]
    
    try:
        # Switching to llama3.2 (2GB) which is MUCH faster than llama3.1 (5GB)
        print("Thinking (using fast llama3.2 model)...")
        response = ollama.chat(
            model='llama3.2',
            messages=messages,
            tools=tools_schema
        )
        
        # Check if the LLM decided to use a tool
        if response.get('message', {}).get('tool_calls'):
            for tool_call in response['message']['tool_calls']:
                func_name = tool_call['function']['name']
                args = tool_call['function']['arguments']
                
                if func_name in available_tools:
                    await update.message.reply_text(f"⏳ *Agent action:* Running `{func_name}`...", parse_mode='Markdown')
                    
                    # Execute the tool
                    tool_result = available_tools[func_name](**args)
                    
                    # Feed the result back to the LLM so it can formulate a final reply
                    messages.append(response['message'])
                    messages.append({
                        'role': 'tool',
                        'name': func_name,
                        'content': tool_result
                    })
                    
                    print("Tool executed. Asking Ollama to summarize the result...")
                    final_response = ollama.chat(model='llama3.2', messages=messages)
                    reply_text = final_response['message']['content']
                    await update.message.reply_text(reply_text)
                    return
                    
        # If no tools were called, just return the text response
        reply_text = response['message']['content']
        await update.message.reply_text(reply_text)
        
    except Exception as e:
        print(f"ERROR: {e}")
        await update.message.reply_text(f"Error: {e}")

def main():
    print("Starting Upgraded Telegram Agent with Tool Capabilities...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Agent is listening for your messages on Telegram...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
