# 📅 Google Calendar MCP Server

> **A powerful Model Context Protocol (MCP) server that lets Claude interact with your Google Calendar seamlessly!**

Transform Claude into your personal calendar assistant with full Google Calendar integration. Create meetings, check schedules, manage events, and more - all through natural conversation with Claude.

## 🌟 What Can This Do?

### ✨ **Smart Calendar Management**
- 📋 **View all your calendars** - See every calendar you have access to
- 📅 **Check your schedule** - Get today's events or upcoming events for any timeframe  
- 🎯 **Create meetings instantly** - Set up Google Meet events with attendees
- ❌ **Cancel events** - Remove events you no longer need
- 🔍 **Search events** - Find events within specific date ranges

### 🤖 **Claude Integration Examples**
Ask Claude things like:
- *"What meetings do I have today?"*
- *"Schedule a team standup for tomorrow at 10 AM with the engineering team"*
- *"Cancel my 3 PM meeting on Friday"*
- *"What's my schedule looking like next week?"*
- *"Create a Google Meet for our client review next Tuesday"*

## 🚀 Quick Start

### Step 1: Prerequisites
- Python 3.8 or higher
- A Google account with Calendar access
- Nango account for authentication (handles Google OAuth for you)

### Step 2: Installation

```bash
# Clone or download the MCP server files
git clone <your-repo-url>
cd google-calendar-mcp

# Install required packages
uv sync
```

### Step 3: Set Up Environment Variables

Create a `.env` file in the project directory:

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` with your Nango credentials:

```bash
# Required Nango Configuration
NANGO_NANGO_BASE_URL=https://api.nango.dev
NANGO_NANGO_SECRET_KEY=your_nango_secret_key_here 
NANGO_CONNECTION_ID=your_connection_id_here
NANGO_INTEGRATION_ID=your_integration_id_here
```

> **🔧 Need help with Nango setup?** Check the [Nango Setup Guide](#nango-setup-guide) below!

### Step 4: Configure Claude Desktop

Add this configuration to your Claude Desktop settings:

**On macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**On Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "google-calendar": {
      "command": "uvx",
      "args": ["git+https://github.com/Shameerpc5029/google-calendar-mcp.git"],
      "env": {
        "NANGO_NANGO_BASE_URL": "https://api.nango.dev",
        "NANGO_NANGO_SECRET_KEY": "your_nango_secret_key_here",
        "NANGO_CONNECTION_ID": "your_connection_id_here", 
        "NANGO_INTEGRATION_ID": "your_integration_id_here"
      }
    }
  }
}
```

### Step 5: Test It Out!

1. **Restart Claude Desktop** completely
2. **Start a new conversation** with Claude
3. **Ask Claude:** *"What meetings do I have today?"*

If everything is set up correctly, Claude will be able to access your Google Calendar! 🎉

## 🛠️ Available Tools

| Tool | Description | Example Use |
|------|-------------|-------------|
| `get_all_calendars` | List all your Google Calendars | *"Show me all my calendars"* |
| `get_calendar_events` | Get events from a specific calendar | *"What's on my work calendar this week?"* |
| `create_meet_event` | Create a new event with Google Meet | *"Schedule a team meeting for Friday at 2 PM"* |
| `cancel_calendar_event` | Delete/cancel an event | *"Cancel my 3 PM meeting today"* |
| `get_today_events` | Get today's events | *"What's my schedule today?"* |
| `get_upcoming_events` | Get upcoming events | *"What do I have coming up next week?"* |

## 🔧 Nango Setup Guide

Nango handles the complex Google OAuth flow for you. Here's how to set it up:

### 1. Create a Nango Account
- Go to [Nango.dev](https://nango.dev) and sign up
- Create a new project

### 2. Set Up Google Calendar Integration
- In your Nango dashboard, add a new integration
- Choose "Google Calendar" as the provider
- Follow Nango's guide to configure Google OAuth credentials

### 3. Get Your Credentials
- **NANGO_SECRET_KEY**: Found in your Nango project settings
- **NANGO_CONNECTION_ID**: Created when a user connects their Google account
- **NANGO_INTEGRATION_ID**: The ID of your Google Calendar integration

### 4. Test Your Connection
```bash
# Test that your environment is set up correctly
python -c "import os; print('✅ All env vars set!' if all([os.getenv('NANGO_CONNECTION_ID'), os.getenv('NANGO_INTEGRATION_ID'), os.getenv('NANGO_NANGO_SECRET_KEY')]) else '❌ Missing env vars')"
```

## 🧪 Testing Your Setup

### Option 1: Test with MCP Inspector
```bash
# Install the MCP inspector
npm install -g @modelcontextprotocol/inspector

# Test your server
npx @modelcontextprotocol/inspector python main.py
```

### Option 2: Direct Python Test
```bash
# Run the server directly to see if it starts without errors
python main.py
```

### Option 3: Test with Claude
Ask Claude: *"Can you check what calendar tools are available?"*

## 🔍 Troubleshooting

### Common Issues

**❌ "Failed to retrieve calendars"**
- Check your Nango credentials in `.env`
- Verify your Google Calendar connection in Nango dashboard
- Ensure the Google account has calendar access

**❌ "NANGO_CONNECTION_ID environment variable is required"**
- Make sure your `.env` file is in the same directory as the Python script
- Check that all environment variables are set correctly
- Restart Claude Desktop after making changes

**❌ Claude can't find the calendar tools**
- Verify the full path in your Claude config is correct
- Make sure you restarted Claude Desktop completely
- Check the Claude Desktop logs for error messages

### Getting Help

1. **Check the logs**: Claude Desktop shows MCP server logs in its developer console
2. **Test your .env**: Run `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.environ.get('NANGO_CONNECTION_ID'))"`
3. **Verify file paths**: Make sure all paths in your Claude config are absolute paths

## 📋 Example Usage with Claude

Once set up, you can have natural conversations with Claude about your calendar:

**You:** *"What's my schedule looking like today?"*

**Claude:** *I'll check your calendar for today's events.*
```json
{
  "success": true,
  "events": [
    {
      "summary": "Team Standup",
      "start": "2024-01-15T09:00:00Z",
      "end": "2024-01-15T09:30:00Z"
    }
  ],
  "total_events": 1
}
```
*You have 1 event today: Team Standup from 9:00 AM to 9:30 AM.*

---

**You:** *"Schedule a client meeting for next Friday at 2 PM with john@company.com"*

**Claude:** *I'll create that meeting for you with a Google Meet link.*
```json
{
  "success": true,
  "event": {
    "summary": "Client Meeting",
    "start": "2024-01-19T14:00:00Z",
    "attendees": [{"email": "john@company.com"}]
  }
}
```
*✅ Created "Client Meeting" for Friday, January 19th at 2:00 PM with john@company.com. Google Meet link has been included automatically.*

## 🔐 Security & Privacy

- **Your credentials**: Stored locally in your `.env` file - never shared
- **Google access**: Managed through Nango's secure OAuth flow
- **Data handling**: All calendar data stays between your Google account, Nango, and Claude
- **No data storage**: This MCP server doesn't store any of your calendar information

## 🤝 Contributing

Found a bug or want to add a feature? 

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - feel free to use this in your own projects!

---

**🎉 Enjoy your new AI-powered calendar assistant!** 

If you found this helpful, consider starring the repository and sharing it with others who might benefit from AI calendar management.