# Discord Ticket Bot

A Discord moderation bot that allows users to create support tickets via DM. Staff members with a designated role can claim and respond to tickets through DMs.

## Features

- **DM-based Ticketing**: Users can DM the bot to create a ticket
- **Staff Notifications**: All staff members receive a DM when a new ticket is created
- **Claim System**: Staff can claim tickets with a button click
- **Two-way Communication**: Messages are relayed between user and staff member via DMs
- **Ticket Management**: Close tickets and view all open tickets
- **Persistent Storage**: Tickets are saved to a JSON file

## How It Works

1. **User creates a ticket**: User sends a DM to the bot
2. **Staff get notified**: All users with the staff role receive a DM with ticket details and a "Claim" button
3. **Staff claims ticket**: A staff member clicks the "Claim Ticket" button
4. **Communication begins**: Messages between the user and staff member are relayed through the bot
5. **Ticket closed**: Either party can close the ticket with the `!close` command

## Setup Instructions

### 1. Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section on the left sidebar
4. Click "Add Bot"
5. Under "Privileged Gateway Intents", enable:
   - ✅ Message Content Intent
   - ✅ Server Members Intent
6. Click "Reset Token" and copy your bot token (keep this secret!)

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the Bot Token

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and replace `your_bot_token_here` with your actual bot token:
   ```
   DISCORD_BOT_TOKEN=your_actual_token_here
   ```

### 4. Invite the Bot to Your Server

1. In the Discord Developer Portal, go to "OAuth2" → "URL Generator"
2. Select these scopes:
   - ✅ `bot`
3. Select these bot permissions:
   - ✅ Send Messages
   - ✅ Read Messages/View Channels
   - ✅ Embed Links
   - ✅ Attach Files
   - ✅ Read Message History
   - ✅ Add Reactions
4. Copy the generated URL and open it in your browser to invite the bot

### 5. Run the Bot

```bash
python ticket_bot.py
```

### 6. Configure the Staff Role(s)

In your Discord server, run this command (you need Administrator permissions):

```
!setup @StaffRole1 @StaffRole2 @StaffRole3
```

You can specify one or multiple roles. All members with any of these roles will receive ticket notifications.

Alternatively, you can add roles one at a time:
```
!add_staff_role @ModRole
```

## Commands

### For Administrators
- `!setup @role1 @role2 ...` - Set up the bot with one or more staff roles
- `!add_staff_role @role` - Add an additional staff role
- `!remove_staff_role @role` - Remove a staff role
- `!view_staff_roles` - View all configured staff roles

### For Everyone
- `!close` - Close your current ticket (works for both users and staff)

### For Staff
- `!tickets` - View all open tickets

## Usage

### For Users
1. Send a DM to the bot with your issue/question
2. The bot will create a ticket and notify staff
3. Wait for a staff member to claim your ticket
4. Once claimed, you can have a conversation via DMs
5. Use `!close` when you're done

### For Staff
1. You'll receive a DM when a new ticket is created
2. Click "Claim Ticket" to handle it
3. Reply to the user via DM (the bot will relay messages)
4. Use `!close` when the issue is resolved
5. Use `!tickets` to see all open tickets

## File Structure

```
ticket_bot.py       # Main bot code
requirements.txt    # Python dependencies
.env.example       # Example environment variables
.env               # Your bot token (create this)
tickets.json       # Ticket storage (auto-generated)
config.json        # Bot configuration (auto-generated)
```

## Troubleshooting

**Bot doesn't respond to DMs:**
- Make sure Message Content Intent is enabled in the Developer Portal
- Restart the bot after enabling intents

**Staff not receiving notifications:**
- Make sure you've run `!setup @StaffRole` or `!add_staff_role @StaffRole` in the server
- Check that staff members have DMs enabled
- Use `!view_staff_roles` to confirm roles are configured correctly

**"Missing Permissions" error:**
- Make sure the bot has the required permissions in your server
- Check that the bot role is above other roles it needs to interact with

## Notes

- The bot stores tickets in `tickets.json` - don't delete this while the bot is running
- Configuration is stored in `config.json`
- Only one ticket per user at a time
- Tickets can only be claimed by one staff member

## Support

If you have issues, make sure:
1. All intents are enabled in the Developer Portal
2. The bot has proper permissions in your server
3. Staff members have DMs enabled from server members
4. You've run the `!setup` command

Enjoy your new ticket bot! 🎫
