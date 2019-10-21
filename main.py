#!/bin/python3

from bs4 import BeautifulSoup as bs
import requests
import os
import configparser
import time
import logging

WUECAMPUSURL = "https://wuecampus2.uni-wuerzburg.de/"
BASEPATH = "./"
LOGPATH = "downloader.log"
CHECKUPTIME = 3600


class WueCampus:
    """WueCampus Connection"""

    session = None

    def __init__(self, url, user, pw, path):
        # set initial parameters
        self.url = url
        self. user = user
        self.password = pw
        self.base_path = path

    def __del__(self):
        self.logout()

    def run(self):
        """General process"""
        self.login()
        semesters = self.get_course_ids()

        # only use most recent available semester
        for course in semesters[0][1]:
            self.download(course[0], [semesters[0][0], course[1]])

        self.logout()

    def login(self):
        """login to moodle"""
        login_url = self.url + "/moodle/login/index.php"
        self.session = requests.Session()
        result = self.session.get(login_url)

        # get token from login page
        html = bs(result.text, 'html.parser')
        token = html.find("input", {"name": "logintoken"}).attrs["value"]

        # set payload
        payload = {
            'logintoken': token,
            'username': self.user,
            'password': self.password
                   }

        # login
        self.session.post(login_url, payload)
        logging.info("Logged in successfully")

    def get_course_ids(self) -> list:
        """Fetches a list of semesters with a sublist of courses and their moodle ids"""
        COURSELIST_CLASS = 'jmu-mycourses'
        SEMESTER_CLASS = 'jmu-mycourses-toggle'
        COURSE_CLASS = 'jmu-mycourses-cat'

        result = self.session.get(self.url + '/moodle/')
        html = bs(result.text, 'html.parser')
        overview = html.find("div", {"class": COURSELIST_CLASS})
        semester_list = list()
        index = -1
        for content in overview.contents:
            # get semesters
            if SEMESTER_CLASS in content.attrs['class']:
                index += 1
                semester_list.append([content.text, list()])
            elif COURSE_CLASS in content.attrs['class']:
                # get course information
                for course in content.contents:
                    course_url = course.attrs['href']
                    semester_list[index][1].append([course_url, course.text])

        return semester_list

    def download(self, course_url, folderlist: list):
        """Download all resources within a course"""

        # get course info
        result = self.session.get(course_url)
        html = bs(result.text, 'html.parser')
        dls = html.find_all("a")

        # get all download urls for resources
        for dl in dls:
            if "href" in dl.attrs and \
                    '/moodle/mod/resource/view.php?id=' in dl.attrs["href"]:
                url = dl.attrs["href"]

                # download resource
                if ".pdf" in url:
                    # no examples available
                    pass
                else:
                    # access dedicated download page
                    temp = self.session.get(url)
                    dl_html = bs(temp.text, 'html.parser')
                    links = dl_html.find_all("a")

                    # create target directory path
                    course_path = self.base_path
                    for folder in folderlist:
                        folder = "".join(s for s in folder if s.isalnum())
                        course_path += folder + "/"

                    # create path if necessary
                    if not os.path.isdir(course_path):
                        os.makedirs(course_path)

                    # download each resource if it does not exist already
                    for link in links:
                        # if "href" in link.attrs:
                        # print(course_path + link.attrs["href"].split("/")[-1])
                        if "href" in link.attrs and (".pdf" or ".zip") in link.attrs["href"] and not os.path.exists(course_path + link.attrs["href"].split("/")[-1]):
                            file = self.session.get(link.attrs["href"])
                            logging.info("Downloading file to " + course_path + link.attrs["href"].split("/")[-1])
                            open(course_path + link.attrs["href"].split("/")[-1], 'wb+').write(file.content)

        # print(folderlist)

    def logout(self):
        """Logs out"""

        # load page info
        page = self.session.get(self.url + "/moodle/")
        html = bs(page.text, 'html.parser')

        # find logout token
        token = html.find('a', {"data-title": "logout,moodle"}).attrs["href"].split("sesskey=")[1]

        # send logout
        self.session.get(self.url + "/moodle/login/logout.php" + "?sesskey=" + token)
        logging.info("Logged out successfully")


def get_config(config_path: str = "./config.ini"):
    """Get configuration settings"""
    ini_parser = configparser.ConfigParser()
    ini_parser.read(config_path)

    # read all options
    user = get_option(ini_parser, "General", "User")
    password = get_option(ini_parser, "General", "Password")
    base_url = get_option(ini_parser, "General", "BaseURL")
    target_dir = get_option(ini_parser, "General", "TargetDir")
    checkup_interval = get_option(ini_parser, "General", "Interval")
    log_path = get_option(ini_parser, "General", "LogPath")

    # set default values
    if (user or password) is None:
        logging.error("Username or Password is missing")
        return None
    if base_url is None:
        base_url = WUECAMPUSURL
    if target_dir is None:
        target_dir = BASEPATH
    if checkup_interval is None:
        checkup_interval = CHECKUPTIME
    if log_path is None:
        log_path = LOGPATH
    return [user, password, base_url, target_dir, checkup_interval, log_path]


def get_option(parser, section, option):
    """Get single setting"""
    try:
        return parser.get(section, option)
    except configparser.NoSectionError or configparser.NoOptionError:
        return None


if __name__ == "__main__":
    options = get_config()
    if options:
        downloader = WueCampus(options[2], options[0], options[1], options[3])
        try:
            FORMAT = '%(asctime)-15s %(message)s'
            logging.basicConfig(filename="downloader.log", level=logging.INFO,
                                format='%(asctime)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            logging.info("Starting Downloader")
            while True:
                downloader.run()
                logging.info("Download Cycle Completed")
                time.sleep(int(options[4]))
        except KeyboardInterrupt:
            downloader.__del__()
            logging.info("Stopped Downloader")
