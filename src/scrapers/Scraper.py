import os
import time
from pathlib import Path
from urllib.parse import quote

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.get_default_browser import get_browser

CHROMIUM_EXE_NAMES = ("chrome.exe", "msedge.exe", "chromium.exe", "opera.exe", "brave.exe", "vivaldi.exe")


class Scraper:
    """Base générique pour scraper un site d'offres d'emploi nécessitant une connexion.

    Chaque site (LinkedIn, Indeed, HelloWork, ...) doit dériver cette classe et se
    contenter de renseigner les attributs de classe ci-dessous (URLs et sélecteurs
    CSS) : toute la logique (lancement du navigateur, connexion, scroll infini,
    extraction, retry) est portée par cette classe.
    """

    # -- Connexion --
    LOGIN_URL = ""
    LOGIN_SUCCESS_URL_CONTAINS = ""
    USERNAME_SELECTOR = "input[type='email']"
    PASSWORD_SELECTOR = "input[type='password']"

    # -- Recherche --
    SEARCH_URL_TEMPLATE = ""  # doit contenir {keyword} et {start}
    CARD_SELECTOR = ""
    CARD_READY_SELECTOR = ""  # sélecteur signalant qu'une carte est pleinement rendue (par défaut = CARD_SELECTOR)

    # -- Extraction d'une offre --
    TITLE_SELECTOR = ""
    TITLE_ATTR = "aria-label"
    LINK_SELECTOR = ""
    LINK_ATTR = "href"
    COMPANY_SELECTOR = ""
    LOCATION_SELECTOR = ""

    def __init__(self, baselink: str, login: str = "", password: str = "", persist_session: bool = True):
        self.baselink = baselink
        self.login = login
        self.password = password
        self.persist_session = persist_session
        self.driver = None

    def _profile_dir(self):
        """Dossier de profil Chrome dédié à ce scraper : les cookies (session
        de connexion incluse) y persistent d'une exécution à l'autre."""
        if not self.persist_session:
            return None
        profile_dir = Path(__file__).resolve().parent.parent / "datas" / "browser_profiles" / type(self).__name__.lower()
        profile_dir.mkdir(parents=True, exist_ok=True)
        return str(profile_dir)

    def _launch_driver(self):
        browser_path = get_browser()
        profile_dir = self._profile_dir()

        if browser_path and browser_path.lower().endswith(CHROMIUM_EXE_NAMES) and os.path.isfile(browser_path):
            try:
                print(f"Navigateur par défaut détecté : {browser_path}")
                return uc.Chrome(browser_executable_path=browser_path, user_data_dir=profile_dir)
            except WebDriverException as e:
                print(f"Impossible d'utiliser le navigateur par défaut ({e}). Bascule sur Selenium standard.")

        print("Utilisation de Selenium standard (chromedriver auto-géré).")
        options = webdriver.ChromeOptions()
        if profile_dir:
            options.add_argument(f"--user-data-dir={profile_dir}")
        return webdriver.Chrome(options=options)

    def _ensure_connected(self):
        if self.driver is not None:
            return
        self.driver = self._launch_driver()
        if self.LOGIN_URL:
            self._login()

    def _login(self):
        driver = self.driver
        driver.get(self.LOGIN_URL)

        if self.LOGIN_SUCCESS_URL_CONTAINS and self.LOGIN_SUCCESS_URL_CONTAINS in driver.current_url:
            print("Session existante réutilisée, connexion sautée.")
            return

        wait = WebDriverWait(driver, 15)
        username_field = wait.until(lambda d: self._first_visible(d, self.USERNAME_SELECTOR))
        username_field.send_keys(self.login)

        password_field = self._first_visible(driver, self.PASSWORD_SELECTOR)
        password_field.send_keys(self.password)
        password_field.send_keys(Keys.RETURN)

        if self.LOGIN_SUCCESS_URL_CONTAINS:
            try:
                wait.until(EC.url_contains(self.LOGIN_SUCCESS_URL_CONTAINS))
            except TimeoutException:
                raise TimeoutException(
                    "Connexion non confirmée après 15s : un contrôle de sécurité "
                    "(CAPTCHA / vérification) bloque probablement la connexion automatisée."
                )
        print("Connecté !")

    def connect(self):
        """Force une (re)connexion et retourne le driver."""
        self.driver = None
        self._ensure_connected()
        return self.driver

    def searchJobs(self, keyword: str, max_results: int = 25, start: int = 0):
        if not self.SEARCH_URL_TEMPLATE or not self.CARD_SELECTOR:
            raise NotImplementedError(
                f"{type(self).__name__} doit définir SEARCH_URL_TEMPLATE et CARD_SELECTOR."
            )

        self._ensure_connected()
        driver = self.driver

        driver.get(self.SEARCH_URL_TEMPLATE.format(keyword=quote(keyword), start=start))

        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.CARD_READY_SELECTOR or self.CARD_SELECTOR)))

        self._loadMoreCards(driver, max_results)

        offers = []
        for _ in range(3):
            cards = driver.find_elements(By.CSS_SELECTOR, self.CARD_SELECTOR)
            offers = [self._extractOffer(card) for card in cards[:max_results]]

            if any(offer["title"] for offer in offers):
                break
            time.sleep(1.5)

        return offers

    def _extractOffer(self, card) -> dict:
        return {
            "title": self._attr_or_empty(card, self.TITLE_SELECTOR, self.TITLE_ATTR),
            "company": self._text_or_empty(card, self.COMPANY_SELECTOR),
            "location": self._text_or_empty(card, self.LOCATION_SELECTOR),
            "link": self._attr_or_empty(card, self.LINK_SELECTOR, self.LINK_ATTR),
        }

    def _loadMoreCards(self, driver, max_results: int, max_attempts: int = 25, pause: float = 1.2):
        # La liste d'offres est en scroll infini dans un panneau interne : il faut le
        # faire défiler progressivement pour que le site charge plus de cartes dans le DOM.
        stable_rounds = 0
        for _ in range(max_attempts):
            count = len(driver.find_elements(By.CSS_SELECTOR, self.CARD_SELECTOR))
            if count >= max_results:
                break

            driver.execute_script(
                """
                const card = document.querySelector(arguments[0]);
                if (!card) return;
                let el = card;
                while (el && el.scrollHeight <= el.clientHeight + 5) {
                    el = el.parentElement;
                }
                if (el) el.scrollTop = Math.min(el.scrollTop + el.clientHeight, el.scrollHeight);
                """,
                self.CARD_SELECTOR,
            )
            time.sleep(pause)

            new_count = len(driver.find_elements(By.CSS_SELECTOR, self.CARD_SELECTOR))
            if new_count <= count:
                stable_rounds += 1
                if stable_rounds >= 3:
                    break
            else:
                stable_rounds = 0

    @staticmethod
    def _first_visible(driver, selector: str):
        for el in driver.find_elements(By.CSS_SELECTOR, selector):
            if el.is_displayed():
                return el
        return False

    @staticmethod
    def _text_or_empty(card, selector: str) -> str:
        if not selector:
            return ""
        try:
            return card.find_element(By.CSS_SELECTOR, selector).text.strip()
        except Exception:
            return ""

    @staticmethod
    def _attr_or_empty(card, selector: str, attr: str) -> str:
        if not selector:
            return ""
        try:
            return card.find_element(By.CSS_SELECTOR, selector).get_attribute(attr) or ""
        except Exception:
            return ""

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
