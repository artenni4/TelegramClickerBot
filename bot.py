import telethon as tl
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest # for skips
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import selenium.common.exceptions 
import urllib.request
import time
import re
import asyncio
from accounts import ACCOUNTS_LIST # list of api_ids and api_hashes
from messages import get_bot_dialogue, balance, withdraw_all
import keyboard


programm_is_running = True # changed by ctrl + shift + ] hotkey, exit while loop if false

async def skip_task(phone, err_msg, arg):
	'''
	Skips task(not always really skips)

	arg -- dictionary, {'tl_bot_chat': bot_chat_variable, 'msg': last_message(not string, but message object),
						'really_skip':True or False(read explanation), 'client': telethon_telgram_client}

	really_skip - some exceptions that occurs while getting on page do not mean that reward won't be given.
	I discovered that only captcha do not allow bot to get reward(see in captcha exception in main()). 
	So if variable is True(only captcha case) we really skip on new task if opposite, wait for default amount
	of seconds and go forward(if we had to wait more, main() will help by waiting new message)
	'''
	print(phone + ': ' + err_msg)
	if arg['really_skip']:
		await arg['client'](GetBotCallbackAnswerRequest(arg['tl_bot_chat'], arg['msg'].id, data=arg['msg'].reply_markup.rows[1].buttons[1].data))
		await asyncio.sleep(3)
	else:
		#define how long to wait
		msg = await arg['client'].get_messages(arg['tl_bot_chat'], limit=1)
		msg = msg[0]
		wait = str(msg.message).replace('You must stay on the site for', '').replace('seconds to get your reward.', '')
		wait = str(wait).replace('Please stay on the site for at least', '').replace('seconds...', '')
		try:
			wait = int(wait)
		except ValueError:
			print('Can not define how long to wait. Standart value is 15 seconds')
			wait = 10

		print('Wait for 15 seconds')
		await asyncio.sleep(wait + 5) # +5 for insurance
		
	print(phone + ': ' + 'Skipped!')
	
        
async def main(browser, accounts_list_slice):
	'''
	Main function where we choose account and talk to bot, then change when we need and repeat

	args:
	browser -- webdriver browser variable
	accounts_list_slice -- list of accounts that change each other if needed(when there is no task for very long)
	'''

	print('Main started...')
	start_session = time.time() # for calculating session duration

	global programm_is_running
	no_ads_iterator = 0 # count how many times there were no ads error
	account_iterator = 0 # read name
	while programm_is_running:
		#log into account
		log_data = accounts_list_slice[account_iterator]
		client = await tl.TelegramClient(log_data['phone'], log_data['api_id'], log_data['api_hash']).start()

		print('**Loged in as: ' + log_data['phone'] + '**')
		PREFIX_ID = log_data['phone'] + ': ' # should be in every print(), shows what number message relates to

		#get ltc bot dialogue
		tl_bot_chat = await get_bot_dialogue(client)
		print(PREFIX_ID + 'Found a LTC Click Bot chat')

		#get new link
		await client.send_message(tl_bot_chat, '/visit')
		print(PREFIX_ID + 'First /visit sent')
		
		#previous setup
		old_msg = None
		msg = await client.get_messages(tl_bot_chat, limit=1)
		msg = msg[0]
		for_skip_task = {'tl_bot_chat': tl_bot_chat, 'msg': None, 'really_skip':False, 'client': client}

		while programm_is_running:
			#wait if bot is lagging
			await asyncio.sleep(2)
			if re.search(r'there are no new ads available', msg.message) and programm_is_running:
				#if there is mo more ad
				no_ads_iterator += 1 #increment

				if no_ads_iterator >= 5:
					#if there is no ads for 5 times -> change account
					print(PREFIX_ID + 'No ads for this account now. Changing account...')
					account_iterator += 1
					if account_iterator >= len(accounts_list_slice):
						account_iterator = 0
					no_ads_iterator = 0 # new account starts at 0 no_ads_iterator
					await client.disconnect()
					break


				found_task = False
				#try for 5 more times
				print(PREFIX_ID + 'No ads observed. It may be a lie. Try /visit for 5 times in a row')
				for i in range(5):
					await client.send_message(tl_bot_chat, '/visit')
					await asyncio.sleep(2)
					msg = await client.get_messages(tl_bot_chat, limit=1)
					msg = msg[0]
					if not re.search(r'there are no new ads available', msg.message):
						#if found task break out of this function and go to the website
						print(PREFIX_ID + 'Found')
						found_task = True
						break
					print(PREFIX_ID + '#{} - No ads'.format(i))

				if not found_task:
					#if bot really do not have tasks for this account
					print(PREFIX_ID + 'Threre is no ad for {} times\nIf there will be no ad for {} times then change account'.format(no_ads_iterator, 5 - no_ads_iterator))
					print(PREFIX_ID + 'There is no more new ad. Sleep for 1 minute')
					print(PREFIX_ID + 'For exit press: ctrl + shift + ]')
					await asyncio.sleep(60) # sleep for a minute and check
					await client.send_message(tl_bot_chat, '/visit')
					print(PREFIX_ID + 'Get up and work!')
					await asyncio.sleep(2)
	

			#set time point before loop
			time_start = time.time()

			#reset msg
			msg = await client.get_messages(tl_bot_chat, limit=1)	
			msg = msg[0]
			#get message
			while msg == old_msg and programm_is_running:
				# exit only if new message
				msg = await client.get_messages(tl_bot_chat, limit=1)
				msg = msg[0]
				await asyncio.sleep(1)

				#check if we have waited for new message for too long
				if time.time() - time_start >= 95:
					try: 
						for_skip_task['msg'] = msg
						for_skip_task['really_skip'] = True
						await skip_task(log_data['phone'], 'There is no new message for too long', for_skip_task)
						for_skip_task['really_skip'] = False
					except AttributeError:
						print(PREFIX_ID + 'Last message was not a link')
						await client.send_message(tl_bot_chat, '/visit')
						await asyncio.sleep(5)
						msg = await client.get_messages(tl_bot_chat, limit=1)
						msg = msg[0]
						for_skip_task['msg'] = msg
						for_skip_task['really_skip'] = True
						try:
							await skip_task(log_data['phone'], 'Try skip for one more time', for_skip_task)
						except AttributeError:
							print(PREFIX_ID + 'Failed one more time')
							break
						finally:
							for_skip_task['really_skip'] = False
			#set new old_msg
			old_msg = msg


			# if got a url
			if re.search(r'Press', msg.message) and programm_is_running:
				no_ads_iterator = 0 # count how many times there were no ads error

				print(PREFIX_ID + 'Ad message sent: {}'.format(msg.date))
				visit_url = msg.reply_markup.rows[0].buttons[0].url
				print(PREFIX_ID + 'Ad URL: ' + visit_url)

				for_skip_task['msg'] = msg # for exceptions

				try: 
					#check for captcha
					url_site = urllib.request.urlopen(visit_url)
					captcha_str = url_site.read().decode('utf-8')
					url_site.close()
					if not re.search(r'reCAPTCHA', captcha_str):
						#go to URL
						browser.get(visit_url)
						print(PREFIX_ID + 'Page was opened succesfully\n\n')
					else:
						for_skip_task['really_skip'] = True
						await skip_task(log_data['phone'], 'Captcha was found on site. Skipping...', for_skip_task)
						for_skip_task['really_skip'] = False
				except selenium.common.exceptions.TimeoutException:
					await skip_task(log_data['phone'], 'Page loading timeout. Skipping...', for_skip_task)
				except TimeoutError:
					for_skip_task['really_skip'] = True
					await skip_task(log_data['phone'], 'Socket timeout. Skipping...', for_skip_task)
					for_skip_task['really_skip'] = False
				except ConnectionResetError:
					await skip_task(log_data['phone'], 'Connection reset. Skipping...', for_skip_task)
				except ConnectionRefusedError:
					await skip_task(log_data['phone'], 'Connection refused. Skipping...', for_skip_task)
				except urllib.error.HTTPError:
					await skip_task(log_data['phone'], 'Can not access the site. Skipping...', for_skip_task)
				except urllib.error.URLError:
					await skip_task(log_data['phone'], 'Bad certificate. Skipping...', for_skip_task)
				except UnicodeDecodeError:
					await skip_task(log_data['phone'], 'Can not decode text for captcha check')
			elif re.search(r'no longer valid', msg.message):
				# if skipped or some error appeared
				await client.send_message(tl_bot_chat, '/visit')
	
	print('Disconnecting with current client')
	await client.disconnect()	


def browser_setup():
	'''
	Setups one browser and returns browser variable
	'''

	#make browser headless
	print('Starting headless browser')
	options = webdriver.firefox.options.Options()
	options.headless = True
	#capabilites = {'browserName': 'chrome'}
	browser = webdriver.Firefox(options=options)	
	browser.implicitly_wait(30)
	print('Browser OK')

	return browser


def stop_working():
	'''
	When user presses ctrl + shift + ] hotkey -> stop program by changing program_is_running variable.
	Do not immediately stops the program, we had to wait until end of while loop
	'''

	global programm_is_running
	programm_is_running = False
	print('Exiting...\nPlease wait for the end, it may take a while')


### PROGRAM STARTS HERE
print('***SESSION STARTED***')

start_session = time.time() # start program timer to show elapsed time in the end

keyboard.add_hotkey('ctrl + shift + ]', stop_working) #bind hotkey for stopping the program
browsers = [] # browsers list
#create browsres list
for _ in range(2): # set in range how many browsers to setup, it may be only one
	browsers.append(browser_setup())


try:
	'''
	Run concurrently several main functions with different browsers
	put in asyncio.gather brackets main functions
	with arguments:
	browser - webdriver browser variable (get it with browser_setup)
	accounts_list_slice - accounts list for given browser (slice because not always pass all counts
	only if one main function was called)
	
	construction of starting program:

	asyncio.get_event_loop().run_until_complete(asyncio.gather(
		main(browsers[0], accounts.ACCOUNTS_LIST[a:b]),
		main(browsers[1], accounts.ACCOUNTS_LIST[c:d]),
		...
		main(browsers[N], accounts.ACCOUNTS_LIST[y:z]) ))

		max N is len(browsers) - 1

	'''
	asyncio.get_event_loop().run_until_complete(asyncio.gather(
		main(browsers[0], [ACCOUNTS_LIST[0]]),
		main(browsers[1], [ACCOUNTS_LIST[1]]) ))
finally:
	# ALWAYS (REALLY FUCKING ALWAYS) close the browsers, otherwise we will run out of RAM
	# I sad ALWAYS, DO NOT FORGET and DO NOT CHANGE finally construction
	for browser in browsers:
		print('Browser shutdown')
		browser.quit() #quit the session

	#calculate and print elapsed time
	secs = time.time() - start_session
	print('Session lapsed for: {0:.1f} seconds or {1:.1f} minutes or {2:.1f} hours'.format(secs, secs / 60, secs / 60 / 60))


print('Exited!')


#decide wether to print balance
if input('Calcualate balance? (1 - yes  0 - no)') == '1':
	asyncio.get_event_loop().run_until_complete(balance())


if input('Withdraw all ltc? (1 - yes  0 - no)') == '1':
	asyncio.get_event_loop().run_until_complete(withdraw_all())






