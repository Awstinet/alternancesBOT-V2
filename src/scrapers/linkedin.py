from .Scraper import Scraper
from config import config


class Linkedin(Scraper):

    LOGIN_URL = "https://www.linkedin.com/login"
    LOGIN_SUCCESS_URL_CONTAINS = "feed"

    SEARCH_URL_TEMPLATE = "https://www.linkedin.com/jobs/search/?keywords={keyword}&start={start}"

    CARD_SELECTOR = "div.job-card-container"
    CARD_READY_SELECTOR = "a.job-card-list__title--link"

    TITLE_SELECTOR = "a.job-card-list__title--link"
    TITLE_ATTR = "aria-label"
    LINK_SELECTOR = "a.job-card-list__title--link"
    LINK_ATTR = "href"
    COMPANY_SELECTOR = ".artdeco-entity-lockup__subtitle"
    LOCATION_SELECTOR = ".artdeco-entity-lockup__caption"


if __name__ == "__main__":
    linkedinScraper = Linkedin(
        "https://www.linkedin.com/jobs/search/",
        config.LINKEDIN_LOGIN,
        config.LINKEDIN_PASSWORD,
    )
    try:
        for page in range(1):
            offers = linkedinScraper.searchJobs("ingénieur", max_results=25, start=25 * page)
            print(f"{len(offers)} offre(s) trouvée(s) :")
            for offer in offers:
                print(offer)
    finally:
        linkedinScraper.close()
