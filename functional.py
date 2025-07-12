import csv
import requests
import json
from PyQt5.QtCore import QThread, pyqtSignal
import asyncio
from aiohttp import ClientSession
from bs4 import BeautifulSoup
import re
from tenacity import retry, stop_after_attempt, wait_fixed
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys

def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
logo_path = resource_path('resources/logo.png')
icon_path = resource_path('resources/icon.ico')

# Lista delle regioni italiane
REGIONI_ITALIA = [
    "Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna", "Friuli-Venezia-Giulia",
    "Lazio", "Liguria", "Lombardia", "Marche", "Molise", "Piemonte", "Puglia", "Sardegna",
    "Sicilia", "Toscana", "Trentino%20Alto%20Adige", "Umbria", "Valle%20d'Aosta", "Veneto"
]

def generate_csv_filename(country, activity, location, all_territory):
    date_str = datetime.now().strftime("%d-%m-%Y")
    location_str = "All" if all_territory else location
    return f"{country}_{activity}_{location_str}_{date_str}.csv"

class WorkerThread(QThread):
    progress_update = pyqtSignal(int, str)
    finished = pyqtSignal()

    def __init__(self, data, tutto_il_territorio=False, parent=None):
        super().__init__(parent)
        self.data = data
        self.tutto_il_territorio = tutto_il_territorio

    def remove_duplicates(self, save_path):
        with open(save_path, 'r', encoding='ISO-8859-1', newline='') as file:
            reader = csv.reader(file, delimiter=';')
            rows = list(reader)
        unique_rows = [rows[0]]

        for row in rows[1:]:
            if row not in unique_rows:
                unique_rows.append(row)

        with open(save_path, 'w', encoding='ISO-8859-1', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerows(unique_rows)

        print(f"Redundancies removed. Cleaned data saved to {save_path}")

    def run(self):
        activity, location = self.data[0]
        save_path = "CSV/" + generate_csv_filename("IT", activity, location, self.tutto_il_territorio)

        with open(save_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["ATTIVITA", "DOVE", "RAGIONE SOCIALE", "INDIRIZZO", "PROVINCIA", "COMUNE", "CAP", "CODLOC", "TELEFONO", "WHATSAPP", "EMAIL", "SITO INTERNET", "DETAILS LINK"])

            total_rows = len(self.data)
            processed_rows = 0

            for attivita, dove in self.data:
                page_number = 1

                while True:
                    try:
                        url = f"https://www.paginegialle.it/ricerca/{attivita}/{dove}/p-{page_number}?output=json"
                        print(url)

                        response = requests.get(url)
                        response.raise_for_status()
                        json_data = response.json()

                        if not json_data.get('list', {}).get('out', {}).get('base', {}).get('results'):
                            print("No data present on page")
                            break

                        json_info = json_data['list']['out']['base']['results']

                        if len(json_info) == 0:
                            break

                        for k in json_info:
                            ds_ragsoc = k.get("ds_ragsoc", "")
                            addr = k.get("addr", "")
                            prov = k.get("prov", "")
                            loc = k.get("loc", "")
                            zip_cod = k.get("ds_cap", "")
                            codloc = k.get("codloc", "")
                            ds_ls_telefoni = ", ".join(k.get("ds_ls_telefoni", []))
                            site_link = k.get("extra", {}).get("site_link", {}).get("url", "")
                            email = ", ".join(k.get("ds_ls_email", []))
                            whatsapp = ", ".join(k.get("ds_ls_telefoni_whatsapp", []))
                            p_link = k.get("extra", {}).get("urlms", "")

                            data = [attivita, dove, ds_ragsoc, addr, prov, loc, zip_cod, codloc, ds_ls_telefoni, whatsapp, email, site_link, p_link]
                            writer.writerow(data)

                        page_number += 1

                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 404:
                            print("No more pages found")
                            break
                        else:
                            print(f"Exception occurred: {e}")
                            break
                    except Exception as e:
                        print(f"Exception occurred: {e}")
                        break

                processed_rows += 1
                progress_percentage = int((processed_rows / total_rows) * 100)
                self.progress_update.emit(progress_percentage, "Collecting contacts")

        self.finished.emit()
        self.remove_duplicates(save_path)

class WorkerThreadGermanyAsync(QThread):
    progress_update = pyqtSignal(int, str)
    finished = pyqtSignal()

    def __init__(self, data, tutto_il_territorio=False, parent=None):
        super().__init__(parent)
        self.data = data
        self.tutto_il_territorio = tutto_il_territorio
        self.total_contacts = 0
        self.processed_contacts = 0
        self.total_emails = 0
        self.processed_emails = 0

    def remove_duplicates(self, save_path):
        with open(save_path, 'r', encoding='utf-8', newline='') as file:
            reader = csv.reader(file)
            rows = list(reader)
        unique_rows = [rows[0]]

        for row in rows[1:]:
            if row not in unique_rows:
                unique_rows.append(row)

        with open(save_path, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(unique_rows)

        print(f"Redundancies removed. Cleaned data saved to {save_path}")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def fetch(self, session, url, payload, headers):
        async with session.post(url, data=payload, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    async def extract_mailto_links(self, session, activity, semaphore):
        mailto_links = []
        activity_url = activity['link']
        async with semaphore:  # Limita il numero di coroutines simultanee
            try:
                async with session.get(activity_url) as response:
                    text = await response.text()
                    soup = BeautifulSoup(text, 'html.parser')
                    
                    # Search for "mailto:" links
                    mailto_tags = soup.select('a[href^=mailto]')
                    for tag in mailto_tags:
                        mailto_links.append({
                            'name': activity['name'],
                            'address': activity['address'],
                            'link': activity['link'],
                            'email': tag['href'].split(':')[1].split('?')[0]
                        })
                    
                    # Extract email from 'data-link' attribute of 'email_versenden' div
                    email_div = soup.find('div', id='email_versenden')
                    if email_div:
                        data_link = email_div.get('data-link')
                        if data_link and data_link.startswith('mailto:'):
                            email_address = data_link.split(':')[1].split('?')[0]
                            mailto_links.append({
                                'name': activity['name'],
                                'address': activity['address'],
                                'link': activity['link'],
                                'email': email_address
                            })
                    
                    # Alternative email extraction (in case it's not a mailto link)
                    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    text_content = soup.get_text()
                    found_emails = re.findall(email_regex, text_content)
                    for email in found_emails:
                        mailto_links.append({
                            'name': activity['name'],
                            'address': activity['address'],
                            'link': activity['link'],
                            'email': email
                        })
                
            except Exception as e:
                print(f"No email link found or error occurred for {activity_url}:\n\n {e}")
        
        return mailto_links

    async def fetch_all(self, session, input_what, input_where):
        base_url = "https://www.gelbeseiten.de"
        search_url = f"{base_url}/ajaxsuche"

        all_activity_details = []
        position = 1
        total_results = 0
        fetched_results = 0
        empty_results_count = 0

        async with ClientSession() as session:
            while empty_results_count < 5 and (fetched_results < total_results or fetched_results == 0):
                payload = {
                    "umkreis": -1,
                    "verwandt": False,
                    "WAS": input_what,
                    "WO": input_where,
                    "position": position,
                    "anzahl": 10,
                    "sortierung": "relevanz"
                }
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                
                try:
                    response_json = await self.fetch(session, search_url, payload, headers)
                    html_content = response_json.get('html', '')
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Get pagination info
                    total_results = response_json.get('gesamtanzahlTreffer', 0)
                    actual_results = response_json.get("anzahlTreffer", 0)
                    more_results = response_json.get('anzahlMehrTreffer', 0)
                    fetched_results += actual_results

                    activity_details = self.extract_activity_links_and_details(soup)
                    if not activity_details:
                        empty_results_count += 1
                    else:
                        empty_results_count = 0  # Reset the counter if we get results
                        all_activity_details.extend(activity_details)

                    # Update progress bar
                    progress_percentage = int((fetched_results / total_results) * 100)
                    self.progress_update.emit(progress_percentage, "Collecting contacts")

                    # If there are no more results to fetch, break the loop
                    if more_results == 0:
                        break

                    position += actual_results  # Incrementa di actual_results per la prossima richiesta

                except Exception as e:
                    print(f"\nFailed to load search results: {e}")
                    break

        self.total_contacts = fetched_results
        return all_activity_details

    async def main(self):
        semaphore = asyncio.Semaphore(100)  # Limita a 100 il numero di coroutines simultanee
        all_mailto_links = []

        async with ClientSession() as session:
            tasks = [self.extract_mailto_links(session, activity, semaphore) for activity in self.data]
            total_tasks = len(tasks)
            for idx, task in enumerate(asyncio.as_completed(tasks), 1):
                result = await task
                all_mailto_links.extend(result)
                self.processed_emails = idx
                progress_percentage = int((self.processed_emails / total_tasks) * 100)
                self.progress_update.emit(progress_percentage, "Processing emails")

        return all_mailto_links

    def extract_activity_links_and_details(self, soup):
        activity_details = []
        seen_activities = set()  # Set per tenere traccia delle attività viste
        articles = soup.find_all('article', class_='mod-Treffer')
        for article in articles:
            a_tag = article.find('a', href=True)
            name_tag = article.find('h2', class_='mod-Treffer__name')
            address_tag = article.find('div', class_='mod-AdresseKompakt__adress-text')

            if a_tag and name_tag and address_tag:
                activity_name = name_tag.get_text(strip=True)
                activity_address = address_tag.get_text(strip=True)
                unique_key = (activity_name, activity_address)
                
                if unique_key not in seen_activities:
                    seen_activities.add(unique_key)
                    activity = {
                        'name': activity_name,
                        'address': activity_address,
                        'link': a_tag['href']
                    }
                    activity_details.append(activity)
        return activity_details

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Determina i parametri corretti per la ricerca in base alla checkbox "Tutto il Territorio"
        if self.tutto_il_territorio:
            input_what = self.data[0][0]
            input_where = ""
        else:
            input_what, input_where = self.data[0]

        # Fase 1: Raccolta dei contatti
        all_activity_details = loop.run_until_complete(self.fetch_all(None, input_what, input_where))
        self.progress_update.emit(100, "Collecting contacts")  # Fase completata

        # Converte all_activity_details in un formato corretto per extract_mailto_links
        self.data = [
            {
                'name': activity['name'],
                'address': activity['address'],
                'link': activity['link']
            }
            for activity in all_activity_details
        ]

        # Fase 2: Estrazione delle email
        email_data = loop.run_until_complete(self.main())
        
        save_path = "CSV/" + generate_csv_filename("DE", input_what, input_where, self.tutto_il_territorio)
        with open(save_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Name', 'Address', 'Link', 'Email']
            email_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            email_writer.writeheader()
            for entry in email_data:
                email_writer.writerow({
                    'Name': entry['name'],
                    'Address': entry['address'],
                    'Link': entry['link'],
                    'Email': entry['email']
                })

        self.finished.emit()
        self.remove_duplicates(save_path)

class WorkerThreadChocolate(QThread):
    progress_update = pyqtSignal(int, str)
    finished = pyqtSignal()

    def __init__(self, data, tutto_il_territorio=False, parent=None):
        super().__init__(parent)
        self.data = data
        self.tutto_il_territorio = tutto_il_territorio

    def remove_duplicates(self, save_path):
        with open(save_path, 'r', encoding='utf-8', newline='') as file:
            reader = csv.reader(file)
            rows = list(reader)
        unique_rows = [rows[0]]

        for row in rows[1:]:
            if row not in unique_rows:
                unique_rows.append(row)

        with open(save_path, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(unique_rows)

        print(f"Redundancies removed. Cleaned data saved to {save_path}")

    def run(self):
        search_url = "https://www.local.ch/it/s/"
        input_what, input_where = self.data[0] if not self.tutto_il_territorio else (self.data[0][0], "")

        def get_rid(url):
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'TE': 'Trailers',
            }, allow_redirects=False)
            if response.status_code == 307:
                location = response.headers.get('Location')
                if location:
                    rid = location.split('rid=')[1]
                    return rid
            return None

        def get_total_pages(url):
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'TE': 'Trailers',
            })
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                pagination = soup.find('ol', class_='Pagination_pagesList__H30Dj')
                if pagination:
                    last_page_link = pagination.find_all('a')[-1]
                    if last_page_link:
                        total_pages = int(last_page_link.text)
                        return total_pages
            return 1

        def get_contact_info(contact):
            contact_info = {
                'PhoneContact': [],
                'FaxContact': [],
                'EmailContact': [],
                'URLContact': [],
                'SocialMediaContact': []
            }

            if contact['__typename'] in contact_info:
                contact_info[contact['__typename']].append(contact['value'])
            return contact_info

        def get_data_from_page(page_num, search_url):
            url = f"{search_url}&page={page_num}"
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'TE': 'Trailers',
            })
            data = []

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Trovare il tag <script> con id="__NEXT_DATA__"
                script_tag = soup.find('script', id='__NEXT_DATA__')

                if script_tag:
                    json_content = json.loads(script_tag.string)

                    # Estrarre i dati dal JSON
                    for entry in json_content['props']['pageProps']['data']['search']['entries']:
                        entry_data = {
                            'title': entry['entry']['title'],
                            'localizedCitySlug': entry['entry']['address']['localizedCitySlug'],
                            'PhoneContact': [],
                            'FaxContact': [],
                            'EmailContact': [],
                            'URLContact': [],
                            'SocialMediaContact': []
                        }

                        for contact in entry['entry']['contacts']:
                            contact_info = get_contact_info(contact)
                            for key, value in contact_info.items():
                                entry_data[key].extend(value)
                        
                        for key in ['PhoneContact', 'FaxContact', 'EmailContact', 'URLContact', 'SocialMediaContact']:
                            entry_data[key] = ', '.join(entry_data[key])

                        data.append(entry_data)
                else:
                    print(f"Il tag <script> con id='__NEXT_DATA__' non è stato trovato per la pagina {page_num}.")
            else:
                print(f"Failed to retrieve data for page {page_num}: {response.status_code}")
                print(response.text)

            return data

        def save_to_csv_realtime(data, csv_writer):
            for entry in data:
                csv_writer.writerow(entry)

        # Funzione principale per iterare su tutte le pagine in parallelo e scrivere nel CSV in tempo reale
        def scrape_data_and_write_to_csv(search_url, max_workers=5, filename='contacts.csv'):
            total_pages = get_total_pages(search_url)
            print(f"Total pages found: {total_pages}")

            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['title', 'localizedCitySlug', 'PhoneContact', 'FaxContact', 'EmailContact', 'URLContact', 'SocialMediaContact']
                csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                csv_writer.writeheader()

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_page = {executor.submit(get_data_from_page, page_num, search_url): page_num for page_num in range(1, total_pages + 1)}

                    processed_pages = 0
                    for future in as_completed(future_to_page):
                        page_num = future_to_page[future]
                        try:
                            data = future.result()
                            save_to_csv_realtime(data, csv_writer)
                            processed_pages += 1
                            progress_percentage = int((processed_pages / total_pages) * 100)
                            self.progress_update.emit(progress_percentage, "Processing pages")
                            print(f"Page {page_num} processed.")
                        except Exception as e:
                            print(f"Error processing page {page_num}: {e}")

        search_query = f"{input_what}"
        if input_where:
            search_query += f"%20{input_where}"

        initial_url = f"https://www.local.ch/it/s/{search_query}"
        rid = get_rid(initial_url)

        if rid:
            search_url = f"https://www.local.ch/it/s/{search_query}?rid={rid}"
            filename = "CSV/" + generate_csv_filename("CH", input_what, input_where, self.tutto_il_territorio)
            scrape_data_and_write_to_csv(search_url, filename=filename)
            self.finished.emit()
            self.remove_duplicates(filename)
        else:
            print("Could not retrieve rid.")
            self.finished.emit()
