import subprocess as sb
import time


if __name__ == '__main__':
    
    print('  ________   ______   _        ______   _______     _______     ___     ___       ___ ')
    time.sleep(0.2)
    print(' |__ _ ___| |  ____| | |      |  ____| |  _____|   |  ____ |   /   \   |   \     /   |')
    time.sleep(0.2)
    print('    | |     | |____  | |      | |____  | |  _____  | |___/ |  / / \ \  | |\ \   / /| |')
    time.sleep(0.2)
    print('    | |     |  ____| | |      |  ____| | | |_   _| |  _  _/  | /___\ | | | \ \_/ / | |')
    time.sleep(0.2)
    print('    | |     | |____  | |____  | |____  | |___| |   | | \ \   | |---| | | |  \___/  | |')
    time.sleep(0.2)
    print('    |_|     |______| |______| |______| |_______|   |_|  \_\  |_|   |_| |_|         |_|')
    time.sleep(0.2)
    print('        _______    ______   ________                                                  ')
    time.sleep(0.2)
    print('       |  ____ \  |  __  | |__ _ ___|                                                 ')
    time.sleep(0.2)
    print('       | |____| | | |  | |    | |                                                     ')
    time.sleep(0.2)
    print('       |  ____ /  | |  | |    | |                                                     ')
    time.sleep(0.2)
    print('       | |____|\  | |__| |    | |                                                     ')
    time.sleep(0.2)
    print('       |________| |______|    |_|            By Artenni                               ')
    time.sleep(4)
    print('\n\n')

    print('Log in accounts...')
    sb.run(['python', 'log-in-accounts.py'])

    print('Starting process...')
    #if process gets error then start new in 1 second
    while sb.run(['python', 'bot.py']).returncode != 0:
        time.sleep(3)

