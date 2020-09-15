from accounts import ACCOUNTS_LIST
from telethon import TelegramClient
import telethon.errors.rpcerrorlist
import asyncio

async def go():
	print('If telegram requires to enter the phone,')
	for acc in ACCOUNTS_LIST:
		print('Phone is: ' + acc['phone'])
		try:
			session = await TelegramClient(acc['phone'], acc['api_id'], acc['api_hash']).start()
			await session.disconnect()
		except telethon.errors.rpcerrorlist.PhoneNumberBannedError:
			print('This number is banned, skipping...')

asyncio.get_event_loop().run_until_complete(go())


