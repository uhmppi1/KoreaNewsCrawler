from korea_news_crawler.NaverNewsCommentsCrawler import NaverNewsCommentsCrawler

if __name__ == "__main__":

    # Multiprocessing은 일단 사용하지 않는다.
    Crawler = NaverNewsCommentsCrawler()
    Crawler.set_category("정치", "경제", "생활/문화", "IT/과학", "사회", "세계")  # 정치, 경제, 생활/문화, IT/과학, 사회, 세계 카테고리 사용 가능
    Crawler.set_date_range(2018, 1, 1, 2018, 1, 31)  # 20180101~20180131 까지 크롤링 시작
    # Crawler.crawling("정치")
    Crawler.crawling("경제")
    # Crawler.crawling("생활/문화")
    # Crawler.crawling("IT/과학")
    # Crawler.crawling("사회")
    # Crawler.crawling("세계")
