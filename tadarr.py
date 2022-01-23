from telethon import TelegramClient, events
from telethon.events import common
from telethon.tl.types import DocumentAttributeFilename, DocumentAttributeVideo
from telethon.tl.custom.button import Button
from mimetypes import guess_extension
import radarr
from config import config
from asyncio.exceptions import TimeoutError
from commons import format_bytes

DOWNLOAD_PATH=config["radarr"]["download_folder"]

config = config["telegram"]

bot = TelegramClient('bot', config['client_id'], config['client_secret']).start(bot_token=config['token'])


progress = {}


@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('Send the movie to add to Radarr!')
    raise events.StopPropagation

@bot.on(events.NewMessage(pattern='/progress'))
async def start(event):
    for _, value in progress.items():
        await event.respond("{} - {}/{} downloaded".format(value[2]["title"], format_bytes(value[0]), format_bytes(value[1])))



async def set_progress(movie, received, total):
    progress[movie["id"]] = (received, total, movie)

def getFilename(event: events.NewMessage.Event):
    mediaFileName = "unknown"
    if hasattr(event.media, 'document'):
        for attribute in event.media.document.attributes:
            if isinstance(attribute, DocumentAttributeFilename): 
              mediaFileName=attribute.file_name
              break     
            if isinstance(attribute, DocumentAttributeVideo):
              if event.original_update.message.message != '': 
                  mediaFileName = event.original_update.message.message
              else:    
                  mediaFileName = str(event.message.media.document.id)
              mediaFileName+=guess_extension(event.message.media.document.mime_type)    
     
    mediaFileName="".join(c for c in mediaFileName if c.isalnum() or c in "()._- ")
      
    return mediaFileName


@bot.on(events.NewMessage)
async def echo(event):
    if event.media:
        if hasattr(event.media, 'document'):
            entity = await bot.get_entity(event.chat_id)
            async with bot.conversation(entity) as conv:
                filename = getFilename(event)
                search_results = radarr.search(filename)
                if search_results is False:
                    await conv.send_message("Couldn't determine the movie. Enter the search query manually")
                    query_resp = await conv.get_response()
                    query = query_resp.text
                    search_results = radarr.search(query_resp.text)
                    if search_results is False:
                        await conv.send_message("No movies found with the provided query.")
                        return
                movie_data = radarr.giveTitles(search_results)
                try:
                    for idx, movie in enumerate(movie_data):
                        await conv.send_message("Is this the movie which you are trying to add?")
                        await conv.send_file(movie['poster'])
                        if idx <= len(search_results)-1:
                            await conv.send_message("{} ({})".format(movie['title'], movie['year']),buttons=[Button.inline('Yes', b'yes')])
                        else:
                            await conv.send_message("{} ({})".format(movie['title'], movie['year']), buttons=[Button.inline('Yes', b'yes'),Button.inline('No, show next', b'no')])
                        response = await conv.wait_event(events.CallbackQuery())
                        if response.data == b'yes':
                            if(radarr.inLibrary(movie['id'])):
                                await conv.send_message("This movie already exists in the Library")
                            filename = getFilename(event)
                            await response.answer()
                            await response.reply("Download started!")
                            path = "{0}/{1}".format(DOWNLOAD_PATH,filename)
                            download_callback = lambda received, total: set_progress(movie, received, total)
                            await bot.download_media(event.message, path, progress_callback = download_callback)
                            del progress[movie["id"]]
                            id = radarr.addToLibrary(movie['id'], "/movies")
                            radarr.manualImport(path, id)
                            await conv.send_message("Download complete! {0} is now added to Radarr".format(movie["title"]))
                            break
                        if response.data == b'no':
                            await response.answer()
                except TimeoutError:
                    await conv.send_message("Timeout. Please send again.")

def main():
    bot.run_until_disconnected()

if __name__ == '__main__':
    main()
