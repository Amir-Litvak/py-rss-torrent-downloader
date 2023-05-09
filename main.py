import rss_downloader
import time

def main():
    downloader = rss_downloader.RSSDownloader()
    downloader.run()
    time.sleep(360)
    downloader.stop()

if __name__ == "__main__":
    main()