import os #dir path, startfile
import time #sleep
import sys #exit
import configparser #configparser
import logging
import threading
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
    print("pip install python-qbittorrent")
    sys.exit()

class RSSDownloader:

    def __init__(self):
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
        self._thread = None
        self._run_flag = False
        self._downloaded_items = list()

        
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

    def single_run(self):
        if self._run_flag:
            print("Downloader is alredy running.")
            return
        
        self._download()
           
    def get_downloaded_items(self):
        return self._downloaded_items

    def add_item_to_watchlist(self, item, path = ''):
        with self._lock:
            self._config["WATCHLIST"][item] = path

            with open(f'{self._curr_dir}/config.ini', 'w+') as configfile:
                self._config.write(configfile)

            self._logger.info(f"Added {item} to watchlist")

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
        
    def get_watchlist(self):
        with self._lock:
            watchlist = list(dict(self._config.items(section='WATCHLIST')).keys())

        return watchlist

    def remove_item_from_watchlist(self, item):
        with self._lock:
            if item not in dict(self._config.items(section='WATCHLIST')):
                print(f"{item} not in wathclist")
                return False
            
            self._config["WATCHLIST"].pop(item)
            with open(f'{self._curr_dir}/config.ini', 'w+') as configfile:
                self._config.write(configfile)
            self._logger.info((f"Removed {item} from watchlist"))
            
            return True
        
        
    def get_telegram_token(self):
        with self._lock:
            token = self._config.get('SETTINGS', 'telegram_bot_token')
        
        return token
    
    def _init_config_file(self):
        """Create a new config file"""
        config = configparser.ConfigParser()

        config['SETTINGS'] = {'qbit_path': 'C:/Program Files/qBittorrent/qbittorrent.exe', 
                            'qbit_user': 'your_username',
                            'qbit_password': 'your_password',
                            'port': '8081',
                            'sleep_time': '300',
                            'qbit_integration' : 'yes/no',
                            'telegram_bot_token' : 'TOKEN',
                            'download_dir' : 'C:/Users/USERNAME/Downloads/',
                            'has_dots' : 'no',
                            'must_contain' : ''
                            }
        
        config['WATHLIST'] = {'an item to download' : 'C:/Users/USERNAME/Downloads/item/download/path/'}

        with open(f'{self._curr_dir}/config.ini', 'w+') as configfile:
            config.write(configfile)


    def _run(self):
        while self._run_flag:
            with self._lock:
                sleep_time = self._config.getint('SETTINGS' ,'sleep_time')
                self._logger.info("Checking LisT")
                self._download()
            self._logger.info(f"going to sleep for {sleep_time} seconds")
            time.sleep(sleep_time)
            
    def _download(self):
        #returns a list of (name, value) tuples for each entry in 'WATCHLIST'
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
                        elif not os.path.isfile(f"{self._curr_dir}/Downloads/{entry.title}"):
                            self._dot_torr_download(entry.link, entry.title)
                            self._logger.info(f"Downloaded {entry.title} torrent file to folder")

                        self._downloaded_items.append(entry.title)

        
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
        qb = Client(f"http://127.0.0.1:{self._config.get('SETTINGS', 'port')}/")
        if qb.login(qbit_user, qbit_password) != None:
            print("Error: Wrong qbittorrent username/password")
            self._logger.error("Entered wrong qbittorrent username/password")
            sys.exit()
        
        qb.download_from_link(link, savepath=(dir_path))    

