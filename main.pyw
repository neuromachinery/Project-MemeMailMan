from os import remove,path,listdir,link,chdir,walk
from sys import argv
from discord import File,Intents,Client, Interaction, app_commands,Object
from telebot.async_telebot import AsyncTeleBot
from telebot import ExceptionHandler
from telebot.types import ReactionTypeEmoji
from telebot.apihelper import ApiTelegramException
from threading import Thread,Event
from asyncio import run,sleep,Queue,QueueEmpty,create_task,wait_for,to_thread
from asyncio import exceptions as asyncio_exceptions
from traceback import format_exc
from dotenv import load_dotenv, dotenv_values
from discord import app_commands
from discord.ext import commands
from socketio import AsyncClient,exceptions
from datetime import datetime

import FileManager
from DBconnect import SocketTransiever
from routing import ROUTING

CLI_START_FLAG = Event()
EXIT_FLAG = Event()
exitSignal = EXIT_FLAG.set
SOCKET_TIMEOUT = 15
PROCESS_DELAY = 0.5
HOST = "127.0.0.1"
MMM_PORT = 54323
DB_PORT = 54321
SITE_PORT = 54322 
ADDRESS_DICT = {
    "DB":(HOST,DB_PORT),
    "MMM":(HOST,MMM_PORT),
    "SITE":(HOST,SITE_PORT)
}
#ME = "@Neur0Devil"
ME = 785926638
log_queue = Queue()
get_queue = Queue()
req_queue = Queue()
def get_queue_f():
    try:return get_queue.get_nowait()
    except QueueEmpty:return None


Transiever_queue = Queue()
Transiever = SocketTransiever(ADDRESS_DICT["MMM"])
LOGGER = lambda *args:Transiever.send_message(sock=ADDRESS_DICT["DB"],sender_name=args[0],target_name="DB",message_type="LOG",message=args[1:])


telegram_queue = Queue()
telegram_direct_queue = Queue()
discord_queue = Queue()
site_queue = Queue()
site_direct_queue = Queue()
queues = {telegram_queue,site_queue}


#CWD = path.dirname(argv[0])
CWD = path.dirname(path.realpath(__file__))
chdir(CWD)

load_dotenv()
config = dotenv_values(".env")


SITE_URL = config["SITE_URL"]
DISCORD_TOKEN = config["DISCORD_TOKEN"]
DISCORD_SERVER = int(config["DISCORD_SERVER"])
TELEGRAM_TOKEN = config["TELEGRAM_TOKEN"]
GROUP_ID = config["TELEGRAM_GROUP"]
MUSIC_PATH = config["MUSIC_PATH"]
MEDIA_LIMIT = int(config["MEDIA_LIMIT"])
BOT_KEY = config["BOT_KEY"]

DISCORD_PERMISSIONS = Intents()
DISCORD_PERMISSIONS.messages=True
DISCORD_PERMISSIONS.message_content = True
DISCORD_PERMISSIONS.members = True
DISCORD_PERMISSIONS.guilds = True

FILES_DIRECTORY = FileManager.SharedDirectory
MEDIA_PATH = path.join(CWD,"media")
LOCALE = {
    "RU":{
        "default":"<ошибка>",
        "file_list":"Список всех доступных директорий: ",
        "help":"Список команд: ",
        "arg":"параметр",
        "packing":"Упаковываем файлы",
        "sending":"Отправляем файлы. Кол-во: ",
        "discord_download_desc":"Скачать директорию используя несколько архивов",
        "discord_list_desc":"Отображение доступных директорий",
        "discord_download_param_desc":"Выбранная директория",
        "file_channel_ban":"В этом канале нельзя срать файлами",
        "file_not_found":"Директория не найдена",
        "me_desc":"Ваш ID: ",
        "too_long":"<БОТ: братан, полотна не читаю>",
        "wtf_long":"<БОТ: братан, я такое даже в виде файла не могу прислать, Толстой бы гордился>",
        "":"",
        },
    "EN":{
        "default":"<error>",
        "file_list":"List of accessable directories: ",
        "help":"List of commands: ",
        "arg":"argument",
        "packing":"Packing files",
        "sending":"Sending files. File count: ",
        "discord_download_desc":"Download directory using zip volumes",
        "discord_download_param_desc":"Directory of choice",
        "discord_list_desc":"List of downloadable directories",
        "file_channel_ban":"File-shitting is prohibited for this channel",
        "file_not_found":"Directory not found",
        "me_desc":"Your ID: ",
        "too_long":"<BOT: bruh, not reading all that>",
        "wtf_long":"<BOT: bro threw a book at me>",
        "":"",
        }
    }
locale = lambda arg:LOCALE[CURRENT_LOCALE].get(arg,LOCALE[CURRENT_LOCALE]["default"])
CURRENT_LOCALE = "RU"
FILES_DISCORD_BLACKLIST = [
    936569889999699988,
    922499261319499867,
    1072222440295497748,
    808073771532812301,
    812618354732695574,
    1233431876870606972,
    867905016223105034,
    812614680409276438,
    867803368071495750,
    868491996052983818,
    808077556070219806,
]
FILES_TELEGRAM_BLACKLIST = [
    1,
    32,
    30,
    28,
    418,
    124,
    977,
    34,
]
T_COMMANDS = [
    "download <arg>",
    "list"
]

DISCORD_FILE_LIMIT=int(24.99*1024*1024)
TELEGRAM_UPLOAD_FILE_LIMIT=int(49.9*1024*1024)
TELEGRAM_DOWNLOAD_FILE_LIMIT=int(19.9*1024*1024)

MISCELLANIOUS_LOGS_TABLE = "LogsMisc"
TELEGRAM_LOGS_TABLE = "LogsTelegram"
DISCORD_LOGS_TABLE =  "LogsDiscord"
ROUTING_TABLE = "Routing"
FILE_TABLE = "FilenamesSite"
MUSIC_LOGS_TABLE = "MusicLogs"
MESSAGE_ROOM_TABLE = "MMMRooms"
TABLES = (
    MISCELLANIOUS_LOGS_TABLE,
    TELEGRAM_LOGS_TABLE,
    DISCORD_LOGS_TABLE,
    ROUTING_TABLE,
    FILE_TABLE,
    MUSIC_LOGS_TABLE,
)
CONTENT_LIMIT = 30
def countingSort(arr, exp1): 
    n = len(arr) 
    output = [0] * (n) 
    count = [0] * (10) 
    for i in range(0, n): 
        index = (arr[i][1][0]/exp1) 
        count[int((index)%10)] += 1
    for i in range(1,10): 
        count[i] += count[i-1] 
    i = n-1
    while i>=0: 
        index = (arr[i][1][0]/exp1) 
        output[ count[ int((index)%10) ] - 1] = arr[i]
        count[int((index)%10)] -= 1
        i -= 1
    i = 0
    for i in range(0,len(arr)): 
        arr[i] = output[i] 
def radixSort(arr):
    "Directly sorts lists of such structure: list[tuple[str,tuple[int,int]]]"
    max1 = max(arr,key=lambda val:val[1][0])[1][0]
    exp = 1
    while max1 // exp > 0:
        countingSort(arr,exp)
        exp *= 10
def calculateMemeSpace() -> dict[int,tuple[int,int]]:
    "Calculates a dictionary of modification dates of all downloaded media by their paths, plus a total diskspace by 'total'."
    result = {"total":0}
    for dirpath, dirnames, filenames in walk(MEDIA_PATH,followlinks=True):
        for file in filenames:
            file_path = path.join(dirpath, file)
            size = path.getsize(file_path)
            result["total"] += size
            result[file_path] = int(path.getmtime(file_path)),size
    return result
MemeSpace = calculateMemeSpace()
def purge(amount:int): # TODO
    total = MemeSpace["total"]
    target = total - amount
    memes = list(MemeSpace.items())[1:]
    radixSort(memes)
    purge_amount, i = 0,0
    while total - purge_amount > target:
        purge_amount += memes[i][1][1]
        i+=1
    for meme,_size in tuple(memes[:i]):
        remove(meme)
        del MemeSpace[meme]
    MemeSpace["total"] = total - purge_amount
def readable_string(string:str): 
    return all(ord(char) < 128 or (1040 <= ord(char) <= 1103) for char in string)
def readable_iterable(strings,default:str):
    return next((item for item in strings if readable_string(item)), default)
def buffer_clear():
    [remove(file) for file in listdir(FileManager.Buffer)]
def now():
    return datetime.now().strftime("[%d.%m.%Y@%H:%M:%S]")

class exception_handler(ExceptionHandler):
    def handle(self,exception,*args,**kwargs):
        LOGGER("MMM",MISCELLANIOUS_LOGS_TABLE,(str(exception)+";".join(map(str,args)),now()))
        return True
class Telegram():
    def __init__(self,telegram_queue:Queue,telegram_direct_queue:Queue,exception_handler:ExceptionHandler) -> None:
        self.name = "Telegram"
        self.bot = AsyncTeleBot(TELEGRAM_TOKEN,exception_handler=exception_handler)
        self.queue = telegram_queue
        self.direct_queue = telegram_direct_queue
        self.subscribers = queues.difference({self.queue})
        self.MEDIA_METHODS = {
            'jpg': (self.bot.send_photo,"photo"),
            'jpeg':(self.bot.send_photo,"photo"),
            'png': (self.bot.send_photo,"photo"),
            'gif': (self.bot.send_animation,"animation"),
            'mp4': (self.bot.send_video,"video"),
            'mov': (self.bot.send_video,"video"),
            'avi': (self.bot.send_video,"video")
        }
    async def process_chat(self):
        try:
            message,Path,channel = await self.queue.get()
            channel = ROUTING[ROUTING.index(channel)].ID_to
            user,text,msg_time = message
            too_long_txt = None
            if len(text)>1000:
                if len(text)>10485760:
                    text = locale('wtf_long')
                else:
                    too_long_txt = path.join(CWD,"buffer","too_long.txt")
                    with open(too_long_txt,"w") as file:
                        file.write(text)
                        text = locale('too_long')
            text = f"{user} {msg_time}: \n  {text}"
            keyword_args = {"chat_id":GROUP_ID,"message_thread_id":channel} if type(channel)==int else {"chat_id":channel}
            print(message,Path,channel)
            if(not Path):
                await self.bot.send_message(**keyword_args,text=text)
                return
            ext = Path.split('.')[-1].lower()
        
            with open(Path,"br") as file:
                method,argument_name = self.MEDIA_METHODS.get(ext,self.bot.send_document)
                keyword_args.update({argument_name:file})
                await method(**keyword_args,caption=text)
            #remove(Path)
            if too_long_txt:
                with open(too_long_txt,"r") as file:
                    keyword_args.update({argument_name:file})
                    await self.bot.send_document(**keyword_args,caption=text)
                remove(too_long_txt)
        except Exception:
            E = format_exc()
            LOGGER(self.name,MISCELLANIOUS_LOGS_TABLE,(E,now()))
        finally:self.queue.task_done()
    async def process_direct(self):
        try:
            message,room_uuid,*_ = await self.direct_queue.get()
            user,text,msg_time,*_ = message
            if len(text)>10485760:
                text = locale('wtf_long')
            text = f"{user} -> [{room_uuid}]: \n  {text}"
            message = await self.bot.send_message(chat_id=ME,text=text)
            message_id = message.message_id
            LOGGER(self.name,MESSAGE_ROOM_TABLE,(message_id,room_uuid))
        except Exception:
            E = format_exc()
            LOGGER(self.name,MISCELLANIOUS_LOGS_TABLE,(E,now()))
        finally:self.direct_queue.task_done()
    async def bot_thread(self):
        async def queue_monitor(self:Telegram):
            while not EXIT_FLAG.is_set():
                if(not self.queue.empty()):
                    print(">chat")
                    await self.process_chat()
                if(not self.direct_queue.empty()):
                    print(">direct")
                    await self.process_direct()
                await sleep(1)
                continue
                
        @self.bot.message_handler(commands=["me"])
        async def me(message):
            await self.bot.send_message(message.chat.id,f"{locale('me_desc')}{message.chat.id}")
        @self.bot.message_handler(commands=["start"])
        async def start(message):
            cmds = "\n".join(["/"+cmd.replace('<arg>',locale('arg')) for cmd in T_COMMANDS])
            await self.bot.send_message(message.chat.id,f"{locale('help')}\n{cmds}")
        @self.bot.message_handler(commands=["download"])
        async def file_download(message):
            time = now()
            ret_id = message.chat.id
            if ret_id in FILES_TELEGRAM_BLACKLIST:
                return
            dirname = message.text.removeprefix("/download").strip()
            if not dirname in FileManager.dirList(FILES_DIRECTORY):
                return
            bot_message = await self.bot.send_message(ret_id,locale("packing"),reply_to_message_id=message.message_id)
            zips = FileManager.filePack(dirname,TELEGRAM_UPLOAD_FILE_LIMIT)
            if type(zips)==str:
                LOGGER(self.name,MISCELLANIOUS_LOGS_TABLE,(zips,time))
                buffer_clear()
                return
            zips_amount = len(zips)
            await self.bot.edit_message_text(f"{locale('sending')}{zips_amount}",ret_id,bot_message.message_id)
            for i,zipfile in enumerate(zips,start=1):
                with open(zipfile,"br") as file:
                    await self.bot.send_document(ret_id,file,reply_to_message_id=message.message_id,caption=f"{i}/{zips_amount}")
                remove(zipfile)
        @self.bot.message_handler(commands=["files","list"])
        async def file_list(message):
            ret_id = message.chat.id
            files = ";\n".join(FileManager.dirList(FILES_DIRECTORY))
            text = f'{locale("file_list")}\n{files}'
            await self.bot.send_message(ret_id,text)
        @self.bot.message_handler(commands=["test"])
        async def test(message):
            try:
                request = ((message.from_user.username,message.text,now()),None,30)
                [await queue.put(request) for queue in self.subscribers]
            except Exception:
                    E = format_exc()
                    LOGGER(self.name,MISCELLANIOUS_LOGS_TABLE,(str(E),now()))
        @self.bot.message_handler(commands=["language"])
        async def language(message):
            "Changes between two locale options"
            locales = tuple(LOCALE.keys())
            CURRENT_LOCALE = locales[not locales.index(CURRENT_LOCALE)]
        @self.bot.message_handler(func=lambda message:message.chat.type=="private" and message.audio)
        async def audio_upload(message):
            "Uploads audio from user to media server"
            try:
                time = now()
                text = message.text if message.text else message.caption
                media = message.audio
                user = message.from_user
                user = readable_iterable((user.full_name,user.first_name,user.last_name,user.username),user.id)
                ext = media.mime_type
                file = await self.bot.get_file(media.file_id)
                filename = f"{media.title} - {media.performer}.{ext}" if media.title and media.performer else f"{media.file_unique_id}.{ext}"
                Path = path.join(MUSIC_PATH,filename)
                file_bytes = await self.bot.download_file(file.file_path)
                with open(Path,"wb") as f:
                    f.write(file_bytes)
                LOGGER(self.name,MUSIC_LOGS_TABLE,(user,filename,media.title,media.performer,text,time))
            except Exception:
                    E = format_exc()
                    LOGGER(self.name,MISCELLANIOUS_LOGS_TABLE,(str(E),now()))
        @self.bot.message_handler(func=lambda message:message.chat.type=="private" and message.reply_to_message)
        async def direct_message(message):
            Transiever.send_message(ADDRESS_DICT["DB"],sender_name="MMM",target_name="DB",message_type="GET",message=(MESSAGE_ROOM_TABLE,"message_id",message.reply_to_message.message_id,))
            data = Transiever.receive_message(timeout=SOCKET_TIMEOUT)
            if not data:
                await self.bot.set_message_reaction(ME, message.id, [ReactionTypeEmoji('💔')], is_big=False)
                return
            room_uuid = data["message"][0][1]
            await site_direct_queue.put((("Neur0Devil",message.text,message.date),room_uuid))
            await self.bot.set_message_reaction(ME, message.id, [ReactionTypeEmoji('❤')], is_big=False)
        @self.bot.message_handler(content_types=["text","sticker","photo","video","gif"])
        async def messages(message):
            time = now()
            if(not (channel:=message.message_thread_id) in ROUTING):
                LOGGER(self.name,MISCELLANIOUS_LOGS_TABLE,(f"{channel} не смотрим",time))
                return
            text = message.text if message.text else message.caption
            text = "" if not text else text
            user = message.from_user
            user = readable_iterable((user.full_name,user.first_name,user.last_name,user.username),user.id)
            if(not (message.photo or message.video or message.sticker)):
                LOGGER(self.name,TELEGRAM_LOGS_TABLE,(user,message.text,"",time,message.message_thread_id))
                request = ((user,text,time),None,channel)
                [await queue.put(request) for queue in self.subscribers]
                return
            ext = "png" if message.photo or (message.sticker and not message.sticker.is_video) else "mp4"
            media = next((var for var in (message.photo,message.video,message.sticker) if var),None) # define media by what there is in the message.
            media = media[-1] if isinstance(media,list) else media # if it's message.photo
            LOGGER(self.name,TELEGRAM_LOGS_TABLE,(user,text,media.file_unique_id,time,message.message_thread_id))
            Path = path.join(MEDIA_PATH,f"{media.file_unique_id}.{ext}")
            if MemeSpace["total"]+TELEGRAM_DOWNLOAD_FILE_LIMIT>=MEDIA_LIMIT:
                purge(TELEGRAM_DOWNLOAD_FILE_LIMIT)
            with open(Path,"wb") as pic:
                file = await self.bot.get_file(media.file_id)
                pic.write(await self.bot.download_file(file.file_path))
                MemeSpace["total"] += file.file_size
            request = ((user,text+f" {media.file_unique_id}.{ext}",time),Path,channel)
            [await queue.put(request) for queue in self.subscribers]
        _ = create_task(queue_monitor(self))
        await self.bot.polling() 
    def main(self): 
        while not EXIT_FLAG.is_set():
            try:
                run(self.bot_thread())
            except Exception:
                E = format_exc()
                LOGGER(MISCELLANIOUS_LOGS_TABLE,(str(E),now()))
                EXIT_FLAG.set()
class Site():
    def __init__(self,site_queue:Queue,site_direct_queue:Queue,*args,**kwargs):
        self.name = "MMM_SITE"
        self.server_url = SITE_URL
        self.server_path = None
        self.queue = site_queue
        self.direct_queue = site_direct_queue
        self.subscribers = queues.difference({self.queue})
        self.sio = AsyncClient()
        self.connected = False
        self.sio.on('connect', self.on_connect,namespace="/chat")
        self.sio.on('disconnect', self.on_disconnect,namespace="/chat")
        self.sio.on('receive_message', self.on_message,namespace="/chat")

        self.sio.on('connect', self.on_direct_connect,namespace="/direct")
        self.sio.on('disconnect', self.on_direct_disconnect,namespace="/direct")
        self.sio.on('message', self.on_direct_message,namespace="/direct")
        self.sio.on('room_registered', self.on_room_register, namespace="/direct")
    async def connect(self):
        await self.sio.connect(self.server_url,headers={"bot":BOT_KEY},namespaces=["/chat","/direct"],wait=True,retry=10)
    async def disconnect(self):
        await self.sio.disconnect()
        self.direct_connected, self.connected = False,False
    async def on_room_register(self, data):
        print(f"Direct room registered: {data['room_uuid']}")
    async def send_message(self, message, namespace):
        await self.sio.emit('send_message', message,namespace=namespace)
    def on_direct_connect(self):
        print(f'Direct connected: {self.sio.sid}')
        self.direct_connected = True
    def on_connect(self):
        print(f'Server connected: {self.sio.sid}')
        self.connected = True
        if self.server_path:return
        Transiever.send_message(ADDRESS_DICT["SITE"],"MMM","SITE","GET","CWD+UPLOADS")
        try:
            message = Transiever.receive_message(timeout=SOCKET_TIMEOUT)
            self.server_path = message["message"]
        except TimeoutError:
            print("Site unresponsive")
    def on_direct_disconnect(self):
        print("Direct disconnected")
        self.direct_connected = False
    def on_disconnect(self):
        print("Server disconnected")
        self.connected = False
    def on_direct_message(self,data):
        request = ((data["name"],data["message"],data["time"],None,None),data["room_uuid"])
        print(request)
        telegram_direct_queue.put_nowait(request)
    def on_message(self, data):
        if "external" in data and data["external"]:
            return
        filepath = None
        if data["unique_id"]:
            file_id = data["unique_id"]
            Transiever.send_message(ADDRESS_DICT["DB"],"MMM","DB","GET",(FILE_TABLE,"uuid4",file_id))
            extention = None
            try:
                message = Transiever.receive_message(timeout=SOCKET_TIMEOUT)
                if message:
                    extention = path.join(MEDIA_PATH,message["message"][0][1]).split(".")[-1]
                else:
                    print("DB sent this: ", message)                
            except TimeoutError:
                print("DB unresponsive")
            filepath = path.join(MEDIA_PATH,f"{file_id}.{extention}")
            link(path.join(self.server_path,file_id),filepath)
        
        request = ((data["name"],data["message"],data["time"]),filepath,data["channel"])
        print(request)
        [queue.put_nowait(request) for queue in self.subscribers]
    async def process_queue(self):
        while not EXIT_FLAG.is_set():
            try:
                await self.connect()
                while not EXIT_FLAG.is_set():
                    queues_empty = self.queue.empty(),self.direct_queue.empty()
                    if(all(queues_empty)):
                        await sleep(0.5)
                    if(not queues_empty[0]):
                        thing = await self.queue.get()
                        message,path,channel = thing
                        user,text,time = message
                        if not channel in ROUTING or ROUTING[::-1][ROUTING.index(channel)].ID_to != -1:
                            continue
                        await self.send_message({"name":user,"time":time,"message":text,"unique_id":path,"channel":channel,"external":True},namespace="/chat")
                        self.queue.task_done()    
                    if(not queues_empty[1]):
                        thing = await self.direct_queue.get()
                        message,room_uuid,*_ = thing
                        user,text,time,*_ = message
                        await self.send_message({"name":user,"time":time,"message":text,"room_uuid":room_uuid},namespace="/direct")
                        self.direct_queue.task_done()  
                    
            except exceptions.ConnectionError as E:
                print(str(E))
            except asyncio_exceptions.CancelledError:quit()
            except Exception:
                E = format_exc()
                LOGGER(self.name,MISCELLANIOUS_LOGS_TABLE,(E,now()))
                print(E)
            finally:
                await self.disconnect()
    
    def start(self):
        try:
            run(self.process_queue())
        except KeyboardInterrupt:quit()


class DiscordBot(Client):
    def __init__(self, discord_queue:Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "Discord"
        self.tree = app_commands.CommandTree(self)
        self.queue = discord_queue
        self.subscribers = queues.difference({self.queue})
    async def send_file(self, text, file_path, channel):
        channel = self.get_channel(channel)
        if not channel:return
        if text: await channel.send(text)
        if file_path: 
            await channel.send(file=File(file_path))
            remove(file_path)
    
    async def on_message(self,message): 
        if (message.author == self.user):
            return
        time = now()
        if (not (channel:=message.channel.id) in ROUTING):
            LOGGER(self.name,MISCELLANIOUS_LOGS_TABLE,(f"{channel} не смотрим",time))
            return
        file_path = None
        user = message.author
        user = readable_iterable((user.display_name,user.name,user.global_name),user.id)
        for attachment in message.attachments:
            file_path = path.join(MEDIA_PATH,attachment.filename)
            await attachment.save(file_path)
            LOGGER(self.name,DISCORD_LOGS_TABLE,(user,"",attachment.filename,time,channel))
            request = ((user,attachment.filename,time),file_path,channel)
            [await queue.put(request) for queue in self.subscribers]
        LOGGER(self.name,DISCORD_LOGS_TABLE,(user,message.content,"",time,channel))
        request = ((user,message.content,time),None,channel)
        [await queue.put(request) for queue in self.subscribers]
    async def check_queue_and_send(self):
        while not EXIT_FLAG.is_set():
            if self.queue.empty():
                await sleep(1)
                continue
            message,path,channel = await self.queue.get()
            user,text,msg_time = message
            channel = ROUTING[ROUTING.index(channel)].ID_to
            await self.send_file(f"{user} {msg_time}: \n  {text}",path,channel)
            self.queue.task_done()
        self.close()
bot = DiscordBot(discord_queue,intents=DISCORD_PERMISSIONS)
@bot.tree.command(
    name="list",
    description=locale("discord_list_desc"),
    guild=Object(id=DISCORD_SERVER)
)
async def list_cmd(interaction):
    files = "\n".join(FileManager.dirList(FILES_DIRECTORY))
    text = f'{locale("file_list")}\n{files}'
    await interaction.response.send_message(text)
@bot.tree.command(
    name="download",
    description=locale("discord_download_desc"),
    guild=Object(id=DISCORD_SERVER)
)
async def download_cmd(interaction,directory:str):
    time = now()
    ret_id = interaction.channel_id
    if ret_id in FILES_DISCORD_BLACKLIST:
        text = locale("file_channel_ban")
        await interaction.response.send_message(text)
        return
    dirname = directory
    if not dirname in FileManager.dirList(FILES_DIRECTORY):
        text = locale("file_not_found")
        await interaction.response.send_message(text)
        return
    await interaction.response.send_message(locale("packing"))
    zips = FileManager.filePack(dirname,DISCORD_FILE_LIMIT)
    if type(zips)==str:
        await interaction.followup.send(zips)
        LOGGER(bot.name,MISCELLANIOUS_LOGS_TABLE,(zips,time))
        buffer_clear()
        return
    zips_amount = len(zips)
    await interaction.followup.send(f"{locale('sending')}{zips_amount}")
    for i,zipfile in enumerate(zips,start=1):
        with open(zipfile,"br") as file:
            #await interaction.followup.send(f"{i}/{zips_amount}",file=File(file))
            await interaction.followup.send(file=File(file))
        remove(zipfile)
@bot.event
async def on_ready():
    _ = bot.loop.create_task(bot.check_queue_and_send())
    await bot.tree.sync(guild=Object(id=DISCORD_SERVER))
    CLI_START_FLAG.set()
Thread(target=Telegram(telegram_queue,telegram_direct_queue,exception_handler()).main,daemon=True,name="TELEGRAM").start() 
#Thread(target=bot.run,args=[DISCORD_TOKEN],kwargs={"log_handler":None},daemon=True,name="DISCORD").start()
print("started")
while True:
    try:Site(site_queue,site_direct_queue).start()
    except KeyboardInterrupt:
        EXIT_FLAG.set()
        run(bot.close())
        buffer_clear()
        quit()
    except Exception:
        E = format_exc()
        LOGGER("MMM",MISCELLANIOUS_LOGS_TABLE,E,now())