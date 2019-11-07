#!/bin/python3

from bs4 import BeautifulSoup as bs
import requests
import os
import sys
import configparser
import logging

WUECAMPUSURL = "https://wuecampus2.uni-wuerzburg.de/"
BASEPATH = "./"
LOGPATH = "downloader.log"
CWD = os.path.dirname(os.path.realpath(sys.argv[0]))


class WueCampus:
    """WueCampus Connection"""

    session = None

    def __init__(self, url, user, pw, path):
        # set initial parameters
        self.url = url
        self. user = user
        self.password = pw
        self.base_path = path
        self.logged_in = False

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
        self.logged_in = True
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
        logging.debug("Logged in successfully")

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


    def logout(self):
        """Logs out"""
        if not self.logged_in:
            return

        self.logged_in = False

        # load page info
        page = self.session.get(self.url + "/moodle/")
        html = bs(page.text, 'html.parser')

        # find logout token
        token = html.find('a', {"data-title": "logout,moodle"}).attrs["href"].split("sesskey=")[1]

        # send logout
        self.session.get(self.url + "/moodle/login/logout.php" + "?sesskey=" + token)
        logging.debug("Logged out successfully")


def get_config(config_path: str = os.path.join(CWD, "./config.ini")):
    """Get configuration settings"""
    ini_parser = configparser.ConfigParser()
    ini_parser.read(config_path)
    result = dict()

    # read all options
    result["user"] = get_option(ini_parser, "General", "User")
    result["password"] = get_option(ini_parser, "General", "Password")
    result["base_url"] = get_option(ini_parser, "General", "BaseURL")
    if get_option(ini_parser, "General", "TargetDir") is not None:
        result["target_dir"] = os.path.join(CWD, get_option(ini_parser, "General", "TargetDir"))
    if get_option(ini_parser, "Logging", "LogPath") is not None:
        result["log_path"] = os.path.join(CWD, get_option(ini_parser, "Logging", "LogPath"))
    result["log_level"] = get_option(ini_parser, "Logging", "LogLevel")

    # set default values
    if ("user" or "password") not in result:
        logging.error("Username or Password is missing")
        return None
    if "base_url" not in result:
        result["base_url"] = WUECAMPUSURL
    if "target_dir" not in result:
        result["target_dir"] = os.path.join(CWD, BASEPATH)
    if "log_path" not in result:
        result["log_path"] = os.path.join(CWD, LOGPATH)
    return result


def get_option(parser, section, option):
    """Get single setting"""
    try:
        return parser.get(section, option)
    except configparser.NoSectionError:
        return None
    except configparser.NoOptionError:
        return None


if __name__ == "__main__":
    options = get_config()
    if options:
        downloader = WueCampus(options["base_url"], options["user"], options["password"], options["target_dir"])
        try:
            FORMAT = '%(asctime)-15s %(message)s'
            logging.basicConfig(filename=options["log_path"], level=logging.INFO,
                                format='%(asctime)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S', filemode='w')
            logging.debug("Running with following Configuration: " + str(options))
            downloader.run()
            logging.info("Download Cycle Completed")

        except KeyboardInterrupt:
            downloader.__del__()
            logging.error("Hard exit of the downloader by manual interrupt")
