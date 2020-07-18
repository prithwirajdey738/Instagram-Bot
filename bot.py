from selenium import webdriver
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import shelve
import datetime


class InstagramBot:
    def __init__(self, username, password):
        self.username = username  # our username
        self.password = password  # our password
        self.base_url = "https://www.instagram.com"  # base url of instagram
        self.tag_url = "https://www.instagram.com/explore/tags/{}/"  # searching tags

        self.driver = webdriver.Chrome("chromedriver.exe")  # access driver
        self.login()  # login

    def login(self):
        self.driver.get("{}/accounts/login/".format(self.base_url))
        self.driver.implicitly_wait(10)

        self.driver.find_element_by_name('username').send_keys(self.username)
        self.driver.find_element_by_name('password').send_keys(self.password)
        self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/'
                                          'article/div/div[1]/div/form/div[4]/button').click()
        time.sleep(2)

    def search_tag(self, tag):
        self.driver.get(self.tag_url.format(tag))  # search for a particular tag
        self.driver.implicitly_wait(10)  # wait for tag to load

    def nav_user(self, user):  # find a user
        self.driver.get("{}/{}".format(self.base_url, user))
        self.driver.implicitly_wait(10)

    def find_buttons(self, button_text):  # find buttons on page
        buttons = []
        if button_text == 'Follow':
            buttons = self.driver.find_elements_by_xpath("//*[text()='{}']".format(button_text))
        elif button_text == 'Following':
            buttons = self.driver.find_elements_by_xpath('//*[@id="react-root"]/section/main/div/header/section/'
                                                         'div[1]/div[2]/span/span[1]/button')
        elif button_text == 'Unfollow':
            buttons = self.driver.find_elements_by_xpath("//*[text()='{}']".format(button_text))
        return buttons

    def follow_user(self, user):  # follow a user
        self.nav_user(user)
        follow_buttons = self.find_buttons('Follow')
        for btn in follow_buttons:
            btn.click()

    def unfollow_user(self, user):  # unfollow user
        self.nav_user(user)
        unfollow_buttons = self.find_buttons('Following')
        if unfollow_buttons:
            for btn in unfollow_buttons:  # click button
                btn.click()
                unfollow_confirmation = self.find_buttons('Unfollow')[0]  # confirm for private accounts
                unfollow_confirmation.click()
        else:
            print('No {} buttons were found.'.format('Following'))

    def scroll(self):
        self.last_height = self.driver.execute_script("return document.body.scrollHeight")  # returns current height
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # scrolls down
        time.sleep(1)  # sleep

        self.new_height = self.driver.execute_script("return document.body.scrollHeight")  # new height
        if self.new_height == self.last_height:  # if height remains same, we reached end
            return True
        self.last_height = self.new_height  # else set old height as new height
        return False

    def get_img_urls(self, tag, s):
        self.search_tag(tag)
        finished = False
        while not finished:
            imgs = self.driver.find_elements_by_class_name('eLAPa')
            time.sleep(1)

            for img in imgs:
                try:
                    img.click()
                    time.sleep(1)
                    buttons = self.find_buttons('Follow')
                    if buttons:
                        # check if follow/ following button is found
                        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(
                            (By.XPATH, "/html/body/div[4]/div[2]/div/article/header/"
                                       "div[2]/div[1]/div[2]/button")))
                        # now get the inner html
                        inner_html = self.driver.find_element_by_xpath(
                            "/html/body/div[4]/div[2]/div/article/header/"
                            "div[2]/div[1]/div[2]/button").get_attribute('innerHTML')
                        # if it a follow button, we click it
                        if inner_html == "Follow":
                            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                                (By.XPATH, "/html/body/div[4]/div[2]/div/article/header/"
                                           "div[2]/div[1]/div[2]/button"))).click()
                            # wait for acc name to load
                            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(
                                (By.XPATH, "/html/body/div[4]/div[2]/div/article/header/div[2]/"
                                           "div[1]/div[1]/span/a")))
                            # attach account name to list along with date of following
                            acc = self.driver.find_element_by_xpath(
                                "/html/body/div[4]/div[2]/div/article/header/div[2]/"
                                "div[1]/div[1]/span/a").get_attribute('innerHTML')
                            s.append((acc, datetime.date.today().day, datetime.date.today().month, datetime.date.today().year))

                    # close button
                    WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                        (By.XPATH, "/html/body/div[4]/div[3]/button"))).click()
                except:
                    pass
                if len(s) >= 15:  # maximum number of people you want to follow at a time
                    return s
            finished = self.scroll()  # scroll down


if __name__ == "__main__":
    igBot = InstagramBot("pic.gasm.1999", "Prdo@1999")
    print("What operation do you want to perform?", end='\n')
    print("1. Follow people", end='\n')
    print("2. Unfollow people", end='\n')
    option = int(input())
    if option == 1:
        tag = input("Enter the tag you want to search for: ")
        s = list()
        s = igBot.get_img_urls(tag, s)
        db = shelve.open("Accounts")
        for tup in s:
            db[tup[0]] = [tup[1], tup[2], tup[3]]

    elif option == 2:
        db = shelve.open("Accounts")
        initial_size = len(db)
        today = [datetime.date.today().day, datetime.date.today().month, datetime.date.today().year]
        for key in db.keys():
            follow_date = db[key]  # when we followed that user
            if follow_date[2] == today[2]:  # if same year
                if follow_date[1] == today[1]:  # same month
                    if int(follow_date[0]) - int(today[0]) >= 3:  # unfollow after 3 days
                        igBot.unfollow_user(key)
                        db.pop(key)
                else:  # different month, unfollow
                    igBot.unfollow_user(key)
                    db.pop(key)
            else:  # different year, unfollow
                igBot.unfollow_user(key)
                db.pop(key)



