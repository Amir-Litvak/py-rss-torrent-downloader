from qbittorrent import Client
import feedparser
import subprocess
import os
import time
import configparser
import json

def run_script():
    config_file = configparser.ConfigParser()
    config_file.read(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')

    while(True):
        check_and_download(config_file, 'TRACKER')

        time.sleep(config_file.getint('SETTINGS', 'sleep_time'))

def check_and_download(config_file, tracker):
    watch_list = get_list(config_file.get(tracker, 'list_dir')) 
    for item in watch_list:
        if watch_list[item] == None:
            dir_path = (config_file.get(tracker, 'download_dir') + item + "/")
        else:
            dir_path = watch_list[item]

        # for trackers that name their torrents with dots intsead of spaces
        if config_file.get(tracker, 'has_dots') == 'yes':
            item = item.replace(" ", ".") 

        # parse rss feed from link
        feed = feedparser.parse(config_file.get(tracker, 'rss_link'))
        
        for entry in feed['entries']:
            # if item is found in entries, satisfies additional rules,
            # and does not exist already in your directory.
            if item in entry.title and \
            (check_rules(config_file, tracker, entry) == True) and \
            os.path.isfile(dir_path + entry.title) == False:
               
                # open qbitorrent.exe (if not running already) and login to webUI
                qbit_download(config_file, dir_path, entry)

                # add item name to downloaded log
                log_downloaded(config_file, entry)

def get_list(list_path):
    with open(os.path.dirname(os.path.abspath(__file__)) + '/' + list_path) as f:
        data = f.read()

    return json.loads(data)

def check_rules(config_file, tracker, entry):
    if config_file.get(tracker, 'special_rules') != 'no':
        rules = config_file.get(tracker, 'special_rules').split(",")
        for rule in rules:
            if rule not in entry.title:
                return False

    return True

def qbit_download(config_file, dir_path, entry):
    subprocess.Popen(config_file.get('SETTINGS', 'qbit_path'))
    qb = Client('http://127.0.0.1:' + config_file.get('SETTINGS', 'port') + '/')
    qb.login(config_file.get('SETTINGS', 'qbit_user'), config_file.get('SETTINGS', 'qbit_password'))
    qb.download_from_link(entry.link, savepath=(dir_path))

def log_downloaded(config_file, entry):
    with open(os.path.dirname(os.path.abspath(__file__)) + '/' + config_file.get('SETTINGS', 'downloaded_list_dir'), "a+") as f:
        f.write(entry.title + ",\n")

run_script()