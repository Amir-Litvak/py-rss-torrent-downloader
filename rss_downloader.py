import os #dir path, startfile
import sys #exit
import configparser #configparser
import logging #logging
import threading #thread
import datetime #for the logs
import requests #for .torrent downloads


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
    print("pip install python-qbittorrent")
    sys.exit()

class RSSDownloader:

    def __init__(self):
        """
        Create a new RSS downloader instance,
        and read the config.ini file.

        if config.ini does not exist,
        a new config.ini will be created and would need
        changing to fit the user.

        Methods
        -------
        download()
            Runs a downloading cycle exactly once,
            return a list of downloaded items

        add_item_to_watchlist(item, path)
            adds a new item and (optionally) its path to the watchlist

        remove_item_from_watchlist(item)
            Removes an item from the watchlist

        change_setting(setting, att)
            changes one of the settings

        get_watchlist()
            Get the current watchlist
        
        get_settings()
            Get a dictionary of the settings and their attributes as pairs  
        
        get_telegram_token()
            a Telegram specific method to get the bot token

        """
        self._curr_dir = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(f"{self._curr_dir}/.logs", exist_ok=True)
        os.makedirs(f"{self._curr_dir}/Downloads", exist_ok=True)
        self._logger = logging.getLogger()
        logging.basicConfig(filename=f'{self._curr_dir}/.logs/{datetime.date.today()}.log',
                        format='%(asctime)s %(levelname)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S',
                        level=logging.INFO)

        if not os.path.isfile(f'{self._curr_dir}/config.ini'):
            self.__init_config_file()

        self._config = configparser.ConfigParser()
        self._config.read(f'{self._curr_dir}/config.ini')
        self._lock = threading.Lock()

    def download(self):
        #returns a list of (name, value) tuples for each entry in 'WATCHLIST'
        downloaded_items = list()
        
        with self._lock:
            rss_link = self._config.get('SETTINGS', 'rss_link_magent') if \
                            (self._config.get('SETTINGS', 'download_method') == 'magnet') else \
                            self._config.get('SETTINGS', 'rss_link_torr')
                
            feed = feedparser.parse(rss_link)
            
            watch_list = self._config.items(section="WATCHLIST")
            for item, dir_path in watch_list:
                if dir_path == '':
                    dir_path = f"{self._config.get('SETTINGS', 'download_dir')}{item.title()}/"

                # for trackers that name their torrents with dots intsead of spaces
                if self._config.getboolean('SETTINGS', 'has_dots'):
                    item = item.replace(" ", ".")

                for entry in feed['entries']:
                    # if item is found in entry titles (lowercased), satisfies additional rules,
                    # and does not exist already in directory.
                    if item in entry.title.lower() and \
                    self._check_rules('SETTINGS', entry.title) and \
                    not (os.path.isfile(dir_path + entry.title) or \
                         os.path.isdir(dir_path + entry.title)):
                        self._logger.info(f"Found new entry of {item.title()}")
                        # magnet link OR .torrent download
                        if self._config.getboolean('SETTINGS', 'qbit_integration') and \
                            self._config.get('SETTINGS', 'download_method') == 'magnet':   
                            self._qb_web(dir_path, entry.link)
                            self._logger.info(f"Added {entry.title} to qBitorrent")
                        elif not os.path.isfile(f"{self._curr_dir}/Downloads/{entry.title}.torrent"):
                            self._dot_torr_download(entry.link, entry.title)

                        downloaded_items.append(entry.title)

        return downloaded_items

    def add_item_to_watchlist(self, item: str, path: str = '') -> None:
        """ Adds an item to the watchlist along with an optional path """
        with self._lock:
            self._config["WATCHLIST"][item] = path

            with open(f'{self._curr_dir}/config.ini', 'w+') as configfile:
                self._config.write(configfile)

            self._logger.info(f"Added {item} to watchlist")

    def change_setting(self, setting: str, att: str):
        """ Changes attribute at setting """
        with self._lock:
            self._config['SETTINGS'][setting] = att
            with open(f'{self._curr_dir}/config.ini', 'w+') as configfile:
                self._config.write(configfile)

    def get_settings(self) -> dict:
        """ Get all the current settings and their attributes as a dictionary """
        with self._lock:
            settings_dict = dict(self._config.items(section='SETTINGS'))

            return settings_dict
        
    def get_telegram_integration_status(self) -> bool:
        with self._lock:
            return self._config.getboolean('SETTINGS', 'telegram_integration')
        
    def get_watchlist(self):
        """ Get the current watchlist """
        with self._lock:
            watchlist = dict(self._config.items(section='WATCHLIST'))

        return watchlist

    def remove_item_from_watchlist(self, item: str) -> bool:
        """ Removes an item from the watchlist, 
        returns False if item is not found in the list, and True if found. """
        with self._lock:
            if item not in dict(self._config.items(section='WATCHLIST')):
                print(f"{item} not in wathclist")
                return False
            
            self._config["WATCHLIST"].pop(item)
            with open(f'{self._curr_dir}/config.ini', 'w+') as configfile:
                self._config.write(configfile)
            self._logger.info((f"Removed {item} from watchlist"))
            
            return True
        
        
    def get_telegram_token(self)-> str:
        """ Get the telegram bot token """
        with self._lock:
            token = self._config.get('SETTINGS', 'telegram_bot_token')
        
        return token
    
    def __init_config_file(self):
        """Create a new config file"""
        config = configparser.ConfigParser()

        config['SETTINGS'] = {'qbit_integration' : 'no',
                            'qbit_path' : 'C:/Program Files/qBittorrent/qbittorrent.exe',
                            'qbit_user' : 'username',
                            'qbit_password' : 'passowrd',
                            'qbit_port' : '8081',
                            'telegram_integration' : 'no',
                            'telegram_bot_token' : 'TOKEN',
                            'auto_delete_obsolete' : 'yes',
                            'rss_link_magent' : 'https://subsplease.org/rss/?r=1080',
                            'rss_link_torr' : 'https://subsplease.org/rss/?t&r=1080',
                            'download_dir' : f'{self._curr_dir}/Downloads/',
                            'download_method' : '.torrent file',
                            'has_dots' : 'no',
                            'must_contain' : ''}
        
        config['WATCHLIST'] = {'Item' : 'Path'}
        

        with open(f'{self._curr_dir}/config.ini', 'w+') as configfile:
            config.write(configfile)

        
    def _check_rules(self, tracker, title):
        must_contain = self._config.get(tracker, 'must_contain')
        if must_contain != '':
            rules = must_contain.strip().split(",")
            for rule in rules:
                if rule not in title:
                    return False

        return True

    def _qb_web(self, dir_path,link):
        qbit_user = self._config.get('SETTINGS', 'qbit_user')
        qbit_password = self._config.get('SETTINGS', 'qbit_password')
        qbit_path = self._config.get('SETTINGS', 'qbit_path')
        os.startfile(qbit_path)
        qb = Client(f"http://127.0.0.1:{self._config.get('SETTINGS', 'qbit_port')}/")
        if qb.login(qbit_user, qbit_password) != None:
            print("Error: Wrong qbittorrent username/password")
            self._logger.error("Entered wrong qbittorrent username/password")
            sys.exit()
        
        qb.download_from_link(link, savepath=(dir_path))    

    def _dot_torr_download(self, link, title):
        torr_download = requests.get(url=link, allow_redirects=True)

        with open(f"{self._curr_dir}/Downloads/{title}.torrent", 'wb+') as torr_file:
            torr_file.write(torr_download.content)

