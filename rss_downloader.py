import os #dir path, startfile
import time #sleep
import sys #exit
import configparser #configparser
import logging
import threading
import asyncio
import requests
import datetime

try:
    import feedparser #feedparser
except ImportError:
    print("Module 'feedparser' not installed. Please install it via:")
    print("pip install feedparser")
    sys.exit()

try:
    from qbittorrent import Client #qbitorrent web-UI API
except ImportError:
    print("Module 'qbittorrent' not installed. Please install it via:")
    print("pip install qbittorrent")
    sys.exit()

try:
    import telegram
except ImportError:
    print("Module 'telegram' not installed. Please install it via:")
    print("pip install python-telegram-bot --upgrade")
    sys.exit()

class RSSDownloader:
    class Tracker:
        def __init__(self, options, watchlist):
            self._options = options
            self._watchlist = watchlist
            

        class WatchlistItem:
            def __init__(self):
                pass


    def __init__(self):
        """
        Create a new RSS downloader instance,
        and read the config.ini file.

        if config.ini does not exist,
        a new config.ini will be created and would need
        changing to fit the user.

        Methods
        -------
        run()
            Starts a new downloading loop to constantly check for new items to download from different trackers,
            constant intervals.

        stop()
            Stops the downloading loop.

        add_tracker(tracker_name, rss_link, download_dir, has_dots, must_contain, watch_list)
            adds a new tracker to download from.

        add_item_to_watchlist(tracker, item, path)
            adds a new item to track from a specific tracker

        change_setting(setting, att)
            changes one of the settings
        """
        self._curr_dir = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(f"{self._curr_dir}/.logs", exist_ok=True)
        os.makedirs(f"{self._curr_dir}/Downloads", exist_ok=True)
        self._logger = logging.getLogger()
        logging.basicConfig(filename=f'{self._curr_dir}/.logs/{datetime.date.today()}.log',
                        format='%(asctime)s %(levelname)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S',
                        level=logging.INFO)

        
        """ if not os.path.isfile(f'{self._curr_dir}/config.ini'):
            self.__init_config_file()
            print("a config.ini file has been created, please go over it and change the settings")
            sys.exit() """

        self._config = configparser.ConfigParser()
        self._config.read(f'{self._curr_dir}/config.ini')
        self._lock = threading.Lock()
        self._thread = None
        self._run_flag = False
        self._delete_obsolete()
        self._trackers = self._get_trackers()

        if self._config.getboolean('SETTINGS', 'telegram_integration'):
            try:
                import telegram
            except ImportError:
                print("Module 'telegram' not installed. Please install it via:")
                print("pip install python-telegram-bot --upgrade")
                sys.exit()

        if self._config.getboolean('SETTINGS', 'auto_delete_obsolete'):
            self._delete_obsolete()

        
    def run(self):
        if self._run_flag:
            print("Downloader is alredy running.")
            return
        
        self._run_flag = True
        self._thread = threading.Thread(target=self._run)
        self._thread.start()
        
        
    def stop(self):
        if not self._run_flag:
            print("Downloader is not running.")
            return
        
        self._run_flag = False
        self._thread.join()

    def add_tracker(self, 
                tracker_name = 'SOMETRACKER', 
                rss_link_magent = 'https://trackerdomain.com/rss/?r=1080', 
                rss_link_torr = 'https://trackerdomain.com/rss/?r=1080',
                download_dir = 'path/to/your/download_dir', 
                download_method = 'magnet/torr',
                has_dots = 'no', 
                must_contain = 'example, 1080p',
                watch_list = {'placeholder_item' : 'placeholder_path'}):
        with self._lock:
            self._config[tracker_name.upper()] = {'rss_link_magnet' : rss_link_magent,
                                         'rss_link_torr' : rss_link_torr,
                                    'download_dir' : download_dir,
                                    'download_method' : download_method,
                                    'has_dots' : has_dots,
                                    'must_contain' : must_contain}
            
            self._config[f"{tracker_name.upper()}.WATCHLIST"] = watch_list
            
            with open(f'{self._curr_dir}/config.ini', 'w+') as configfile:
                self._config.write(configfile)

            self._logger.info(f"Added {tracker_name} as a new tracker")
    
    def add_item_to_watchlist(self, tracker, item, path = ''):
        with self._lock:
            self._config[f"{tracker}.WATCHLIST"][item] = path

            with open(f'{self._curr_dir}/config.ini', 'w+') as configfile:
                self._config.write(configfile)

            self._logger.info(f"Added {item} to {tracker} watchlist")

    def change_setting(self, setting, att):
        with self._lock:
            old_attribute = self._config.get('SETTINGS', setting)
            self._config['SETTINGS'][setting] = att
            with open(f'{self._curr_dir}/config.ini', 'w+') as configfile:
                self._config.write(configfile)
            self._logger.info((f"Changed {setting} from {old_attribute} to {att}"))

    def get_settings(self):
        with self._lock:
            settings_dict = dict(self._config.items(section='SETTINGS'))

            return settings_dict
    
    def get_tracker_details(self, tracker):
        with self._lock:
            tracker_dets = tuple((dict(self._config.items(section=tracker)),
                                dict(self._config.items(section=f"{tracker}.WATCHLIST"))))
                
            return tracker_dets

    def _run(self):
        while self._run_flag:
            with self._lock:
                sleep_time = self._config.getint('SETTINGS' ,'sleep_time')
                tracker_list = list(filter(_only_trackers, self._config.sections()))
            for tracker in tracker_list:
                self._logger.info(f"Checking List for {tracker}")
                self._download(tracker)
            self._logger.info(f"going to sleep for {sleep_time} seconds")
            time.sleep(sleep_time)

    def _get_qualified_items(self, tracker):
        qualified_item = {}
        
        with self._lock:
            rss_link = self._config.get(tracker, 'rss_link_magent')
            feed = feedparser.parse(rss_link)

            #returns a list of (name, value) tuples for each entry in WATCHLIST
            watch_list = self._config.items(section=f"{tracker}.WATCHLIST")
            for item, dir_path in watch_list:
                if dir_path == '':
                    dir_path = f"{self._config.get(tracker, 'download_dir')}{item.title()}/"

                # for trackers that name their torrents with dots intsead of spaces
                if self._config.getboolean(tracker, 'has_dots'):
                    item = item.replace(" ", ".")

                for entry in feed['entries']:
                    # if item is found in entry titles (lowercased), satisfies additional rules,
                    # and does not exist already in directory.
                    if item in entry.title.lower() and \
                    self._check_rules(tracker, entry.title) and \
                    not (os.path.isfile(dir_path + entry.title) or \
                         os.path.isdir(dir_path + entry.title)):
                        self._logger.info(f"Found new entry of {item.title()}")
                        qualified_item[entry] = dir_path

                        #Sends out a telegram message to group
                        if self._config.getboolean('SETTINGS', 'telegram_integration'):
                            asyncio.run(self._telegram_notification(msg=f"{entry.title} has been added.", 
                                                            chat_id=self._config.get('SETTINGS', 'telegram_group_chat_id'),
                                                            token=self._config.get('SETTINGS', 'telegram_bot_token')))
                        break
        
        return qualified_item
    
    def _qb_magnet_download(self, qualified_items):
        qbit_user = self._config.get('SETTINGS', 'qbit_user')
        qbit_password = self._config.get('SETTINGS', 'qbit_password')
        qbit_path = self._config.get('SETTINGS', 'qbit_path')
        os.startfile(qbit_path)
        qb = Client(f"http://127.0.0.1:{self._config.get('SETTINGS', 'port')}/")
        if qb.login(qbit_user, qbit_password) != None:
            print("Error: Wrong username/password")
            self._logger.error("Entered wrong username/password")
            sys.exit()
        
        for item, path in qualified_items.items():
            qb.download_from_link(item.link, savepath=path)
            self._logger.info(f"Added {item.title} to qBitorrent")
            
    def _download(self, tracker):
        #returns a list of (name, value) tuples for each entry in 'WATCHLIST'
        with self._lock:
            rss_link = self._config.get(tracker, 'rss_link_magent') if \
                            (self._config.get(tracker, 'download_method') == 'magnet') else \
                            self._config.get(tracker, 'rss_link_torr')
                
            feed = feedparser.parse(rss_link)
            
            watch_list = self._config.items(section=f"{tracker}.WATCHLIST")
            for item, dir_path in watch_list:
                if dir_path == '':
                    dir_path = f"{self._config.get(tracker, 'download_dir')}{item.title()}/"

                # for trackers that name their torrents with dots intsead of spaces
                if self._config.getboolean(tracker, 'has_dots'):
                    item = item.replace(" ", ".")
                

                for entry in feed['entries']:
                    # if item is found in entry titles (lowercased), satisfies additional rules,
                    # and does not exist already in directory.
                    if item in entry.title.lower() and \
                    self._check_rules(tracker, entry.title) and \
                    not (os.path.isfile(dir_path + entry.title) or \
                         os.path.isdir(dir_path + entry.title)):
                        self._logger.info(f"Found new entry of {item.title()}")

                        # magnet link OR .torrent download
                        if self._config.getboolean('SETTINGS', 'qbit_integration') and \
                        self._config.get(tracker, 'download_method') == 'magnet':   
                            self._qb_web(dir_path, entry.link)
                            self._logger.info(f"Added {entry.title} to qBitorrent")
                        elif not os.path.isfile(f"{self._curr_dir}/Downloads/{entry.title}"):
                            self._dot_torr_download(entry.link, entry.title)
                            self._logger.info(f"Downloaded {entry.title} torrent file to folder")

                        #Sends out a telegram message to group
                        if self._config.getboolean('SETTINGS', 'telegram_integration'):
                            asyncio.run(self._telegram_notification(msg=f"{entry.title} has been added.", 
                                                            chat_id=self._config.get('SETTINGS', 'telegram_group_chat_id'),
                                                            token=self._config.get('SETTINGS', 'telegram_bot_token')))
                        break
        
    def _check_rules(self, tracker, title):
        must_contain = self._config.get(tracker, 'must_contain')
        if must_contain != '':
            rules = must_contain.strip().split(",")
            for rule in rules:
                if rule not in title:
                    return False

        return True

    def _check_rules(self, tracker, item, title):

        must_contain = self._config.get(f"{tracker}.WATHCLIST", item)
        if must_contain != '':
            rules = must_contain.strip().split(",")
            if os.path.isabs(rules[0]):
                rules.pop(0)
            for rule in rules:
                if rule not in title:
                    return False

        return True
    
    def _init_config_file(self):
        """Create a new config file"""
        config = configparser.ConfigParser()

        config['SETTINGS'] = {'qbit_path': 'C:/Program Files/qBittorrent/qbittorrent.exe', 
                            'qbit_user': 'your_username',
                            'qbit_password': 'your_password',
                            'port': '8081',
                            'sleep_time': '300',
                            'qbit_integration' : 'yes/no'
                            }
        
        self.add_tracker()

        with open(f'{self._curr_dir}/config.ini', 'w+') as configfile:
            config.write(configfile)


    def _qb_web(self, dir_path,link):
        qbit_user = self._config.get('SETTINGS', 'qbit_user')
        qbit_password = self._config.get('SETTINGS', 'qbit_password')
        qbit_path = self._config.get('SETTINGS', 'qbit_path')
        os.startfile(qbit_path)
        qb = Client(f"http://127.0.0.1:{self._config.get('SETTINGS', 'port')}/")
        if qb.login(qbit_user, qbit_password) != None:
            print("Error: Wrong username/password")
            self._logger.error("Entered wrong username/password")
            sys.exit()
        
        qb.download_from_link(link, savepath=(dir_path))    

    def _dot_torr_download(self, link, title):
        
        torr_download = requests.get(url=link, allow_redirects=True)

        with open(f"{self._curr_dir}/Downloads/{title}.torrent", 'wb+') as torr_file:
            torr_file.write(torr_download.content)

    def _delete_obsolete(self):
        self._delete_old_logs()
        self._delete_old_torrent_files()

    def _delete_old_logs(self):
        cutoff_date = datetime.date.today() - datetime.timedelta(days=7)
        for filename in os.listdir(f"{self._curr_dir}/.logs"):
            file_path = os.path.join(f"{self._curr_dir}/.logs", filename)
            if os.path.isfile(file_path):
                file_date = datetime.datetime.strptime(os.path.splitext(filename)[0], '%Y-%m-%d').date()
                if file_date < cutoff_date and filename.endswith('.log'):
                    os.remove(file_path)
        
        pass

    def _delete_old_torrent_files(self):
        if os.listdir(f"{self._curr_dir}/Downloads"):
            dir_dict = self._get_downlad_dir_dict()
            #check in every save directory for existance of the downloaded file from torrent
            for torrent_file in os.listdir(f"{self._curr_dir}/Downloads"):
                for item, dir in dir_dict:
                    if item in torrent_file and os.path.isfile(f"{dir}/{torrent_file.removesuffix('.torrent')}"):
                        os.remove(f"{self._curr_dir}/Downloads/{torrent_file}")
        

    def _get_downlad_dir_dict(self):
        dir_dict = {}
    
        for tracker in list(filter(_only_trackers, self._config.sections())):
            tracker_has_dots = self._config.getboolean(tracker, 'has_dots')
            tracker_dir = self._config.get(tracker, 'download_dir')
            for item, dir in self._config.items(section=f"{tracker}.WATCHLIST"):
                if tracker_has_dots:
                    item = item.replace(" ", ".")
                if dir:
                    dir_dict[item] = dir
                else:
                    dir_dict[item] = tracker_dir + item.replace(".", " ").title()

        return dir_dict
    
    def _get_trackers(self):
        tracker_list = []
        
        for tracker_name in list(filter(_only_trackers, self._config.sections())):
            tracker_list.append(self.Tracker(tracker_name, ))
    
    async def _telegram_notification(self, msg, token, chat_id):
        bot = telegram.Bot(token)
        async with bot:
            await bot.send_message(text=msg, chat_id=chat_id)

def _only_trackers(section):
    if (section == 'SETTINGS') or ('.' in section):
        return False

    return True
