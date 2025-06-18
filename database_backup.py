import discord
import asyncio

db_name = 'UserData.db'
sticky_sushi_id = 546962882047508481
dry_vegetable_id = 788285654395519007

# Function to keep a backup of the database in case server goes down
async def database_backup(client):
    user = await client.fetch_user(dry_vegetable_id)
    while True: 
        await user.send(file=discord.File(db_name))
        print('Database successfully backed up')
        await asyncio.sleep(21600)