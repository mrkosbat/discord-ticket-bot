import discord
from discord.ext import commands
import json
import os
from datetime import datetime

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# File to store tickets
TICKETS_FILE = 'tickets.json'
CONFIG_FILE = 'config.json'

# Load or create tickets storage
def load_tickets():
    if os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_tickets(tickets):
    with open(TICKETS_FILE, 'w') as f:
        json.dump(tickets, f, indent=4)

# Load or create config
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"guild_id": None, "staff_role_ids": []}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

tickets = load_tickets()
config = load_config()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guild(s)')

@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author.bot:
        return
    
    # Check if message is a DM
    if isinstance(message.channel, discord.DMChannel):
        user_id = str(message.author.id)
        
        # Check if user has an active ticket
        if user_id in tickets and tickets[user_id].get('status') == 'open':
            ticket = tickets[user_id]
            
            # If ticket is claimed, forward message to staff member
            if ticket.get('claimed_by'):
                staff_id = ticket['claimed_by']
                staff_member = await bot.fetch_user(staff_id)
                
                embed = discord.Embed(
                    title=f"Message from {message.author.name}",
                    description=message.content,
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Ticket #{ticket['ticket_id']}")
                
                # Handle attachments
                if message.attachments:
                    attachment_urls = [att.url for att in message.attachments]
                    embed.add_field(name="Attachments", value="\n".join(attachment_urls), inline=False)
                
                try:
                    await staff_member.send(embed=embed)
                    await message.add_reaction('✅')
                except:
                    await message.channel.send("❌ Error sending message to staff member.")
            else:
                await message.channel.send("⏳ Your ticket is waiting to be claimed by a staff member. Please be patient!")
        
        # Check if staff member is replying to a ticket
        elif user_id in [str(t['claimed_by']) for t in tickets.values() if t.get('claimed_by')]:
            # Find which ticket this staff member is handling
            for ticket_user_id, ticket in tickets.items():
                if str(ticket.get('claimed_by')) == user_id and ticket.get('status') == 'open':
                    # Forward message to ticket creator
                    ticket_creator = await bot.fetch_user(int(ticket_user_id))
                    
                    embed = discord.Embed(
                        title=f"Staff Response from {message.author.name}",
                        description=message.content,
                        color=discord.Color.green(),
                        timestamp=datetime.utcnow()
                    )
                    embed.set_footer(text=f"Ticket #{ticket['ticket_id']}")
                    
                    # Handle attachments
                    if message.attachments:
                        attachment_urls = [att.url for att in message.attachments]
                        embed.add_field(name="Attachments", value="\n".join(attachment_urls), inline=False)
                    
                    try:
                        await ticket_creator.send(embed=embed)
                        await message.add_reaction('✅')
                    except:
                        await message.channel.send("❌ Error sending message to user.")
                    break
        else:
            # User doesn't have a ticket, create one
            await create_ticket(message.author, message.content)
    
    await bot.process_commands(message)

async def create_ticket(user, initial_message):
    user_id = str(user.id)
    
    # Check if user already has an open ticket
    if user_id in tickets and tickets[user_id].get('status') == 'open':
        await user.send("❌ You already have an open ticket! Please wait for a staff member to respond.")
        return
    
    # Create new ticket
    ticket_id = len(tickets) + 1
    tickets[user_id] = {
        'ticket_id': ticket_id,
        'user_id': user_id,
        'username': str(user),
        'created_at': datetime.utcnow().isoformat(),
        'initial_message': initial_message,
        'status': 'open',
        'claimed_by': None
    }
    save_tickets(tickets)
    
    # Send confirmation to user
    embed = discord.Embed(
        title="✅ Ticket Created",
        description=f"Your ticket (#{ticket_id}) has been created! A staff member will be with you shortly.",
        color=discord.Color.green()
    )
    await user.send(embed=embed)
    
    # Notify staff members
    if config.get('guild_id') and config.get('staff_role_ids'):
        try:
            guild = bot.get_guild(config['guild_id'])
            if guild:
                notified_users = set()  # Track who we've notified to avoid duplicates
                
                for role_id in config['staff_role_ids']:
                    staff_role = guild.get_role(role_id)
                    if staff_role:
                        for member in staff_role.members:
                            if not member.bot and member.id not in notified_users:
                                notified_users.add(member.id)
                                embed = discord.Embed(
                                    title=f"🎫 New Ticket #{ticket_id}",
                                    description=f"**From:** {user.mention} ({user})\n**Message:** {initial_message}",
                                    color=discord.Color.orange(),
                                    timestamp=datetime.utcnow()
                                )
                                
                                # Create claim button
                                view = ClaimTicketView(ticket_id, user_id)
                                
                                try:
                                    await member.send(embed=embed, view=view)
                                except:
                                    pass  # Staff member has DMs disabled
        except Exception as e:
            print(f"Error notifying staff: {e}")

class ClaimTicketView(discord.ui.View):
    def __init__(self, ticket_id, user_id):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
        self.user_id = user_id
    
    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.green)
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = self.user_id
        
        # Check if ticket is still available
        if user_id not in tickets or tickets[user_id].get('status') != 'open':
            await interaction.response.send_message("❌ This ticket is no longer available.", ephemeral=True)
            return
        
        if tickets[user_id].get('claimed_by'):
            await interaction.response.send_message("❌ This ticket has already been claimed by another staff member.", ephemeral=True)
            return
        
        # Claim the ticket
        tickets[user_id]['claimed_by'] = interaction.user.id
        save_tickets(tickets)
        
        # Notify the staff member
        await interaction.response.send_message(f"✅ You have claimed ticket #{self.ticket_id}! You can now respond to the user via DM.", ephemeral=True)
        
        # Notify the user
        try:
            ticket_creator = await bot.fetch_user(int(user_id))
            embed = discord.Embed(
                title="Staff Member Assigned",
                description=f"**{interaction.user.name}** is now handling your ticket! They will respond shortly.",
                color=discord.Color.green()
            )
            await ticket_creator.send(embed=embed)
        except:
            pass
        
        # Disable the button
        button.disabled = True
        await interaction.message.edit(view=self)

# Commands for staff
@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx, *staff_roles: discord.Role):
    """Setup the bot with staff roles"""
    if not staff_roles:
        await ctx.send("❌ Please provide at least one staff role.\nUsage: `!setup @Role1 @Role2 @Role3`")
        return
    
    config['guild_id'] = ctx.guild.id
    config['staff_role_ids'] = [role.id for role in staff_roles]
    save_config(config)
    
    role_mentions = ", ".join([role.mention for role in staff_roles])
    await ctx.send(f"✅ Bot configured! Staff roles set to: {role_mentions}")

@bot.command()
@commands.has_permissions(administrator=True)
async def add_staff_role(ctx, staff_role: discord.Role):
    """Add an additional staff role"""
    if not config.get('staff_role_ids'):
        config['staff_role_ids'] = []
    
    if staff_role.id in config['staff_role_ids']:
        await ctx.send(f"❌ {staff_role.mention} is already a staff role.")
        return
    
    config['staff_role_ids'].append(staff_role.id)
    save_config(config)
    await ctx.send(f"✅ Added {staff_role.mention} as a staff role.")

@bot.command()
@commands.has_permissions(administrator=True)
async def remove_staff_role(ctx, staff_role: discord.Role):
    """Remove a staff role"""
    if not config.get('staff_role_ids') or staff_role.id not in config['staff_role_ids']:
        await ctx.send(f"❌ {staff_role.mention} is not a staff role.")
        return
    
    config['staff_role_ids'].remove(staff_role.id)
    save_config(config)
    await ctx.send(f"✅ Removed {staff_role.mention} from staff roles.")

@bot.command()
@commands.has_permissions(administrator=True)
async def view_staff_roles(ctx):
    """View all configured staff roles"""
    if not config.get('staff_role_ids'):
        await ctx.send("❌ No staff roles configured. Use `!setup @Role` to set them up.")
        return
    
    guild = ctx.guild
    roles = [guild.get_role(role_id) for role_id in config['staff_role_ids']]
    roles = [role for role in roles if role is not None]  # Filter out deleted roles
    
    if not roles:
        await ctx.send("❌ No valid staff roles found.")
        return
    
    role_list = "\n".join([f"• {role.mention}" for role in roles])
    embed = discord.Embed(
        title="📋 Staff Roles",
        description=role_list,
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command()
async def close(ctx):
    """Close your current ticket (for users or staff)"""
    user_id = str(ctx.author.id)
    
    # Check if user has a ticket
    ticket_to_close = None
    if user_id in tickets and tickets[user_id].get('status') == 'open':
        ticket_to_close = (user_id, tickets[user_id])
    else:
        # Check if staff member is handling a ticket
        for ticket_user_id, ticket in tickets.items():
            if str(ticket.get('claimed_by')) == user_id and ticket.get('status') == 'open':
                ticket_to_close = (ticket_user_id, ticket)
                break
    
    if ticket_to_close:
        ticket_user_id, ticket = ticket_to_close
        tickets[ticket_user_id]['status'] = 'closed'
        tickets[ticket_user_id]['closed_at'] = datetime.utcnow().isoformat()
        save_tickets(tickets)
        
        # Notify both parties
        try:
            user = await bot.fetch_user(int(ticket_user_id))
            await user.send(f"🔒 Ticket #{ticket['ticket_id']} has been closed.")
        except:
            pass
        
        if ticket.get('claimed_by'):
            try:
                staff = await bot.fetch_user(ticket['claimed_by'])
                await staff.send(f"🔒 Ticket #{ticket['ticket_id']} has been closed.")
            except:
                pass
        
        await ctx.send(f"✅ Ticket #{ticket['ticket_id']} has been closed.")
    else:
        await ctx.send("❌ You don't have an active ticket.")

@bot.command()
async def tickets(ctx):
    """View all open tickets (staff only)"""
    # Check if user is staff
    if config.get('guild_id') and config.get('staff_role_ids'):
        guild = bot.get_guild(config['guild_id'])
        if guild:
            member = guild.get_member(ctx.author.id)
            if member:
                user_role_ids = [role.id for role in member.roles]
                is_staff = any(role_id in config['staff_role_ids'] for role_id in user_role_ids)
                
                if is_staff:
                    open_tickets = {k: v for k, v in tickets.items() if v.get('status') == 'open'}
                    
                    if not open_tickets:
                        await ctx.send("📭 No open tickets.")
                        return
                    
                    embed = discord.Embed(
                        title="📋 Open Tickets",
                        color=discord.Color.blue()
                    )
                    
                    for user_id, ticket in open_tickets.items():
                        claimed = "✅ Claimed" if ticket.get('claimed_by') else "⏳ Unclaimed"
                        embed.add_field(
                            name=f"Ticket #{ticket['ticket_id']} - {claimed}",
                            value=f"**User:** {ticket['username']}\n**Created:** {ticket['created_at'][:10]}",
                            inline=False
                        )
                    
                    await ctx.send(embed=embed)
                    return
    
    await ctx.send("❌ You don't have permission to use this command.")

# Run the bot
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    if not TOKEN:
        print("Error: Please set DISCORD_BOT_TOKEN environment variable")
        print("You can get your token from https://discord.com/developers/applications")
    else:
        bot.run(TOKEN)
