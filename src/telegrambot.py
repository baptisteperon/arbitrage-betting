import config
import requests

import asyncio
from telegram import Bot

class TelegramBot:

    def __init__(self):
        """ Sets up new conversation with the bot using it's unique identification token
            timeout : timeout in seconds to wait for the user's response
            offset : integer identifying the last received update
        """
        self.bot = Bot(config.TOKEN)
        self.timeout = 180
        message = 'Starting the program.\nSend any message so that the last update id can be retreived'
        url_message = f'https://api.telegram.org/bot{config.TOKEN}/sendMessage?chat_id={config.chat_id}&text={message}'
        requests.get(url_message)
        url_response = f"https://api.telegram.org/bot{config.TOKEN}/getUpdates?timeout=60"
        response = requests.get(url_response).json()
        status = response['ok']
        result = response['result']
        if (status == True) and (len(result) > 0):
            last_update = len(result)-1   
            last_id = result[last_update]['update_id']
            self.offset = last_id + 1
        else:
            raise Exception('No update, cannot create bot')

    async def send_message(self, message):
        """ Telegram messages are limited to 4096 characters.
            If the message to send is bigger than that, send it in chunks of less than 4096 characters
        """
        if len(message) > 4096:
            message_chunks = message.splitlines()
            while len(message_chunks) > 0:
                length = 0  
                chunk = ''
                ready_to_send = False
                while not ready_to_send:
                    if (len(message_chunks) == 0):
                        ready_to_send = True
                    elif (len(message_chunks[0])+length < 4096):
                        length += len(message_chunks[0]) + 1
                        chunk = chunk + message_chunks.pop(0) + '\n'
                    else:
                        ready_to_send = True
                async with self.bot:
                    await self.bot.send_message(text=chunk, chat_id=config.chat_id)
        else:
            async with self.bot:
                await self.bot.send_message(text=message, chat_id=config.chat_id)

    async def get_response(self):
        """ Getting last response in the chat
        """
        async with self.bot:
            updates = await self.bot.get_updates(timeout=self.timeout, offset=self.offset)
            if len(updates)>0:
                self.offset += 1
                return updates[len(updates)-1]['message']['text']
            else:   # in case the timeout is reached (no answer)
                raise Exception('Timeout, no answer')
            
if __name__ == "__main__":
    """ to test message sending """
    bot = TelegramBot()
    msg = 'test'
    print(len(msg))
    asyncio.run(bot.send_message(msg))