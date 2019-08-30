from korea_news_crawler.NaverNewsCommentsCrawler import NaverNewsCommentsCrawler
import sys

if __name__ == "__main__":

    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print("python run_crawling.py [시작일자(YYYYMMDD)] [종료일자(YYYYMMDD)] [카테고리(정치|경제|..)] [모드(TEST|REAL)-optional/Default=REAL]")
        print("사용예: python run_crawling.py 20180101 20180131 경제")

    start_date = sys.argv[1]
    end_date = sys.argv[2]
    category = sys.argv[3]
    mode_test = False
    if len(sys.argv) == 5:
        if sys.argv[4] == 'TEST' or sys.argv[4] == 'test':
            mode_test = True   #

    # Multiprocessing은 일단 사용하지 않는다.
    Crawler = NaverNewsCommentsCrawler()
    Crawler.set_category("정치", "경제", "생활문화", "IT과학", "사회", "세계")  # 정치, 경제, 생활문화, IT과학, 사회, 세계 카테고리 사용 가능
    Crawler.set_date_range(start_date, end_date)
    Crawler.set_mode_test(mode_test)
    Crawler.crawling(category)

    # Crawler.set_date_range(2018, 1, 1, 2018, 1, 31)  # 20180101~20180131 까지 크롤링 시작
    # Crawler.crawling("정치")
    # Crawler.crawling("경제")
    # Crawler.crawling("생활문화")
    # Crawler.crawling("IT과학")
    # Crawler.crawling("사회")
    # Crawler.crawling("세계")
