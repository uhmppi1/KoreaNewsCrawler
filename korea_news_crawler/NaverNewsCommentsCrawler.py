#!/usr/bin/env python
# -*- coding: utf-8, euc-kr -*-

from time import sleep
from bs4 import BeautifulSoup
from multiprocessing import Process
from korea_news_crawler.exceptions import *
from korea_news_crawler.articleparser import ArticleParser
from korea_news_crawler.articlecrawler import ArticleCrawler
import os
import platform
import calendar
import requests
import re
from datetime import timedelta, date, datetime
import json
from selenium import webdriver
from selenium.common.exceptions import *

class NaverNewsCommentsCrawler(ArticleCrawler):
    def __init__(self):
        self.categories = {'정치': 100, '경제': 101, '사회': 102, '생활문화': 103, '세계': 104, 'IT과학': 105, '오피니언': 110,
                           'politics': 100, 'economy': 101, 'society': 102, 'living_culture': 103, 'world': 104, 'IT_science': 105, 'opinion': 110}
        self.selected_categories = []
        self.date = {}
        self.user_operating_system = str(platform.system())
        print('user_operating_system: ', self.user_operating_system)
        self.wd_path = './webdriver/' + self.user_operating_system + '/chromedriver'
        self.webdriver = webdriver.Chrome(self.wd_path)
        self.init_data_directory()
        self.mode_test = False

    def set_mode_test(self, mode):
        self.mode_test = mode

    def set_date_range(self, start_year, start_month, start_day, end_year, end_month, end_day):

        # 입력받은 파라미터가 invalid하다면 date 생성하면서 오류난다. 굳이 아래 지저분한 체크로직은 필요없다.
        self.date['start'] = date(start_year, start_month, start_day)
        self.date['end'] = date(end_year, end_month, end_day)

        assert (self.date['start'] <= self.date['end'])

        print(self.date)

    def set_date_range(self, start_yyyymmdd, end_yyyymmdd):

        # 입력받은 파라미터가 invalid하다면 date 생성하면서 오류난다. 굳이 아래 지저분한 체크로직은 필요없다.
        self.date['start'] = datetime.strptime(start_yyyymmdd, '%Y%m%d').date()
        self.date['end'] = datetime.strptime(end_yyyymmdd, '%Y%m%d').date()

        assert (self.date['start'] <= self.date['end'])

        print(self.date)

    @staticmethod
    def make_news_page_url(url):
        made_urls = []

        # totalpage는 네이버 페이지 구조를 이용해서 page=10000으로 지정해 totalpage를 알아냄
        # page=10000을 입력할 경우 페이지가 존재하지 않기 때문에 page=totalpage로 이동 됨 (Redirect)
        totalpage = ArticleParser.find_news_totalpage(url + "&page=10000")
        for page in range(1, totalpage + 1):
            made_urls.append(url + "&page=" + str(page))

        return made_urls

    # 1건의 article(기사)의 원문 및 댓글을 크롤링하여 1개의 json object를 리턴하는 메소드..
    # 이 메소드부터는 selenium chrome webdriver를 사용한다.
    def crawling_article(self, content_url, date, category):
        try:
            # 기사 HTML 가져옴
            self.webdriver.get(content_url)
            html = self.webdriver.page_source
            document_content = BeautifulSoup(html, 'lxml')

            # 기사 제목 가져옴
            tag_headline = document_content.find_all('h3', {'id': 'articleTitle'}, {'class': 'tts_head'})
            text_headline = ''  # 뉴스 기사 제목 초기화
            text_headline = text_headline + ArticleParser.clear_headline(
                str(tag_headline[0].find_all(text=True)))
            if not text_headline:  # 공백일 경우 기사 제외 처리
                raise Exception('No text headline')

            # 기사 본문 가져옴
            tag_content = document_content.find_all('div', {'id': 'articleBodyContents'})
            text_sentence = ''  # 뉴스 기사 본문 초기화
            text_sentence = text_sentence + ArticleParser.clear_content(str(tag_content[0].find_all(text=True)))
            if not text_sentence:  # 공백일 경우 기사 제외 처리
                raise Exception('No contents')

            # 기사 언론사 가져옴
            tag_company = document_content.find_all('meta', {'property': 'me2:category1'})
            text_company = ''  # 언론사 초기화
            text_company = text_company + str(tag_company[0].get('content'))
            if not text_company:  # 공백일 경우 기사 제외 처리
                raise Exception('No press information')

            article_obj = {}
            article_obj['url'] = content_url
            article_obj['press'] = text_company
            article_obj['date'] = date
            article_obj['category'] = category
            article_obj['title'] = text_headline
            article_obj['contents'] = text_sentence

            # 댓글 크롤링!!
            article_obj['comments'] = self.crawling_comments(document_content)
            return article_obj

        except Exception as ex:  # UnicodeEncodeError ..
            print(ex)
            return None

    def crawling_comments(self, document_content, sleep_time=0.3, num_comments = 700):
        try:
            self.webdriver.find_element_by_css_selector(".u_cbox_in_view_comment").click()  # 댓글 보기 누르는 코드
            sleep(sleep_time)
        except ElementNotInteractableException as e:
            # print('ElementNotInteractableException')
            return None
        except NoSuchElementException as e:
            # print('NoSuchElementException after u_cbox_in_view_comment')
            try:
                new_addr = document_content.find_all('div', {'class': 'simplecmt_links'})
                new_addr = new_addr[0].select('a')[0]['href']
                self.webdriver.get(new_addr)
                sleep(sleep_time)
            except Exception as e:
                print(e)
                return None
        try:
            self.webdriver.find_element_by_css_selector(".u_cbox_sort_label").click()  # 공감순으로 보기 누르는 코드
            sleep(sleep_time)
        except NoSuchElementException as e:
            # print('NoSuchElementException after u_cbox_sort_label')
            pass

        try:
            for i in range(num_comments // 20):
                # self.webdriver.find_element_by_css_selector(".u_cbox_btn_more").click()  # 댓글 더보기 누르는 코드
                self.webdriver.find_element_by_css_selector(".u_cbox_page_more").click()  # 댓글 더보기 누르는 코드
                sleep(sleep_time)
        except ElementNotVisibleException as e:  # 댓글 페이지 끝
            # print('ElementNotVisibleException')
            pass
        except Exception as e:  # 다른 예외 발생시 확인
            # print('Unknown Exception :', e)
            pass

        try:
            html = self.webdriver.page_source  # 댓글 크롤링 코드
            dom = BeautifulSoup(html, 'lxml')
            comments_raw = dom.find_all('span', {'class': 'u_cbox_contents'})
            comments = [comment.text for comment in comments_raw]
            like_comments_raw = dom.find_all('em', {'class': 'u_cbox_cnt_recomm'})  # 공감수
            like_comments = [like.text for like in like_comments_raw]
            hate_comments_raw = dom.find_all('em', {'class': 'u_cbox_cnt_unrecomm'})  # 비공감수
            hate_comments = [hate.text for hate in hate_comments_raw]
        except Exception as e:  # 다른 예외 발생시 확인
            # print('Unknown Exception :', e)
            pass

        comments_list = list(zip(comments, like_comments, hate_comments))
        comments_obj = [{'comments':a, 'like':b, 'hate':c} for a, b, c in comments_list]
        return comments_obj


    # 특정일자, 특정카테고리의 네이버 기사 및 댓글 하루치를 크롤링하여 1개의 json파일로 저장하는 메소드..
    def crawling_daily(self, category_name, news_date):
        # 기사 URL 형식
        url = "https://news.naver.com/main/list.nhn?mode=LSD&mid=sec&sid1=" + str(
            self.categories.get(category_name)) + "&date=" + news_date

        day_urls = self.make_news_page_url(url)

        # day_urls = day_urls[:2]  # for test

        print(category_name + " Urls are generated")
        print('day_urls length: ', len(day_urls))
        print(day_urls)
        print("The crawler starts..")

        article_list = []
        daily_obj = {'date':news_date}

        for i, URL in enumerate(day_urls):
            request = self.get_url_data(URL)
            document = BeautifulSoup(request.content, 'html.parser')

            # html - newsflash_body - type06_headline, type06
            # 각 페이지에 있는 기사들 가져오기
            post_temp = document.select('.newsflash_body .type06_headline li dl')
            post_temp.extend(document.select('.newsflash_body .type06 li dl'))

            # 각 페이지에 있는 기사들의 url 저장
            post = []
            for line in post_temp:
                post.append(line.a.get('href'))  # 해당되는 page에서 모든 기사들의 URL을 post 리스트에 넣음
            del post_temp

            # post = post[:5]  # for test

            for content_url in post:  # 기사 URL
                article_obj = self.crawling_article(content_url, news_date, category_name)
                article_list.append(article_obj)
                print('crawled : ', content_url)
                # 크롤링 대기 시간
                # sleep(0.01)  # 대기시간이 너무 짧게 설정되어 있다.
                sleep(0.3)

            if self.mode_test:
                daily_obj['articles'] = article_list
                self.save_file(news_date, category_name+'check'+str(i), daily_obj)

        daily_obj['articles'] = article_list
        self.save_file(news_date, category_name, daily_obj)


    def crawling(self, category_name):
        # Multi Process PID
        print(category_name + " PID: " + str(os.getpid()))

        # 기사 URL 형식
        url = "https://news.naver.com/main/list.nhn?mode=LSD&mid=sec&sid1=" + str(
            self.categories.get(category_name)) + "&date="

        print(url)

        def daterange(start_date, end_date):
            for n in range(int((end_date - start_date).days)+1):
                yield start_date + timedelta(n)

        for single_date in daterange(self.date['start'], self.date['end']):  # for each YYYYMMDD:
            news_date = single_date.strftime("%Y%m%d")
            self.crawling_daily(category_name, news_date)


    def init_data_directory(self):
        directory = 'data'
        if not os.path.exists(directory):
            os.mkdir(directory)
        directory = 'data/naver'
        if not os.path.exists(directory):
            os.mkdir(directory)


    def save_file(self, news_date, category_name, article_obj):

        directory = 'data/naver/' + news_date[:6]    # data/YYYYMM
        file_name = directory + '/' + news_date + '_' + category_name + '.json'

        if os.path.exists(directory):
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(article_obj, f, ensure_ascii=False, indent='\t')

        else:
            os.mkdir(directory)
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(article_obj, f, ensure_ascii=False, indent='\t')