from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeFilename, DocumentAttributeVideo
from telethon.tl.custom.button import Button
from mimetypes import guess_extension
import radarr
from config import config

config = config["telegram"]

bot = TelegramClient('bot', config['client_id'], config['client_secret']).start(bot_token=config['token'])


@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('Send the movie to add to Radarr!')
    raise events.StopPropagation

async def set_progress(received, total):
    print(received, total)

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
    download_callback = lambda received, total: set_progress(received, total)
    if event.media:
        if hasattr(event.media, 'document'):
            filename = getFilename(event)
            search_results = radarr.search(filename)
            entity = await bot.get_entity(event.chat_id)
            movie_data = radarr.giveTitles(search_results)
            async with bot.conversation(entity) as conv:
                for idx, movie in enumerate(movie_data):
                    await conv.send_message("Is this the movie which you are trying to add?")
                    await conv.send_file(movie['poster'])
                    if idx <= len(search_results)-1:
                        await conv.send_message("{} ({})".format(movie['title'], movie['year']),buttons=[Button.inline('Yes', b'yes')])
                    else:
                        await conv.send_message("{} ({})".format(movie['title'], movie['year']), buttons=[Button.inline('Yes', b'yes'),Button.inline('No, show next', b'no')])
                    response = await conv.wait_event(events.CallbackQuery())
                    if response.data == b'yes':
                        if(radarr.inLibrary(movie['tmdbId'])):
                            await conv.send_message("This movie already exists in the Library")
                        filename = getFilename(event)
                        await response.answer()
                        await response.reply("Download started!")
                        path = "{0}/{1}".format(config["download_folder"],filename)
                        await bot.download_media(event.message, path, progress_callback = download_callback)
                        id = radarr.addToLibrary(movie['tmdbId'], "/movies")
                        radarr.manualImport(path, id)
                        await conv.send_message("Download complete! {0} is now added to Radarr".format(movie["title"]))
                        break
                    if response.data == b'no':
                        await response.answer()

def main():
    bot.run_until_disconnected()

if __name__ == '__main__':
    main()
