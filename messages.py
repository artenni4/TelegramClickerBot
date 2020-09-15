'''Useful functions file'''

from accounts import ACCOUNTS_LIST # list of api_ids and api_hashes
from telethon import TelegramClient
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
import asyncio
import re

async def get_bot_dialogue(client):
    '''Just get bot dialogue object to use it in further commands'''

    dlgs = await client.get_dialogs()
    for d in dlgs:
        if d.title == 'LTC Click Bot':
        	return d



async def balance():
	'''Calculate balance of all accounts and print them if needed'''

	print('Started summing up all accouts balance...')
	account_balance = 0
	for acc in ACCOUNTS_LIST:
		client = await TelegramClient(acc['phone'], acc['api_id'], acc['api_hash']).start()
		#get ltc bot dialogue
		tl_bot_chat = await get_bot_dialogue(client)
		print('Found a LTC Click Bot chat for ' + acc['phone'])

		await client.send_message(tl_bot_chat, '/balance')
		await asyncio.sleep(2)
		bal = await client.get_messages(tl_bot_chat, limit=1)
		bal = bal[0]
		bal = str(bal.message).replace('Available balance:', '').replace('LTC', '')
		try:
			bal = float(bal)
			account_balance += bal
		except ValueError:
			print('Can not get balance of ' + acc['phone'])
			print('Skipping...')


		await client.disconnect()

	print('Your balance is: {0:.8f}'.format(account_balance))


async def withdraw_all():
	'''Withdraw all balance from all accounts'''

	print('Starting to withdraw...')
	for acc in ACCOUNTS_LIST:
		#log in account
		client = await TelegramClient(acc['phone'], acc['api_id'], acc['api_hash']).start()
		print('Log in as ' + acc['phone'])
		#get bot chat
		tl_bot_chat = await get_bot_dialogue(client)

		#send withdraw request and wait
		await client.send_message(tl_bot_chat, '/withdraw')
		msg = ''
		while not re.search(r'Your balance', msg):
			msg = await client.get_messages(tl_bot_chat, limit=1)
			msg = msg[0].message
			await asyncio.sleep(1)

		#if balance is too small go to nect account
		if re.search(r'Your balance is too small', msg):
			print('Balance is to small to withdraw')
			await client.disconnect()
			continue

		# get balance and send ltc address
		msg = await client.get_messages(tl_bot_chat, limit=1)
		msg = msg[0].message
		bal = float(str(msg).replace('Your balance:', '').replace('To withdraw, enter your Litecoin address:', '').replace('\n', '').replace('LTC', ''))
		ltc_addr = input('Enter ltc address: ')
		await client.send_message(tl_bot_chat, ltc_addr)

		msg = await client.get_messages(tl_bot_chat, limit=1)
		msg = msg[0]
		while not re.search(r'Enter the amount', msg.message):
			msg = await client.get_messages(tl_bot_chat, limit=1)
			msg = msg[0]
			await asyncio.sleep(1)

		#confirm transaction
		await client.send_message(tl_bot_chat, str(bal))
		await asyncio.sleep(2)
		await client.send_message(tl_bot_chat, '/confirm')

		#disconnect from current client
		await client.disconnect()
