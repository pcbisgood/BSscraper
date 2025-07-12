# Y-Corp Business Scrapers 🐼

**Realizzato da Yomi con ☕ & 💛**

## Descrizione

Y-Corp Business Scrapers è un'applicazione desktop multi-piattaforma, sviluppata in Python e PyQt5, che consente di estrarre informazioni commerciali da diverse directory online europee. L'interfaccia grafica, semplice e intuitiva, permette all'utente di selezionare un paese, definire i criteri di ricerca e avviare il processo di raccolta dati, che verranno salvati in un file CSV pulito e pronto all'uso.

## ✨ Funzionalità

- **Interfaccia Grafica Intuitiva**: Un'interfaccia utente in tema scuro facile da usare, costruita con PyQt5.
- **Supporto Multi-Nazione**: Scraper dedicati e ottimizzati per diverse directory nazionali.
- **Scelta del Target**: Seleziona il paese target tramite icone intuitive: 🍕 per l'Italia, 🍺 per la Germania, e 🍫 per la Svizzera.
- **Ricerche Personalizzate**: Inserisci l'attività da cercare (es. "elettricista") e la località (es. "Monza").
- **Ricerca su Territorio Nazionale**: Abilita una checkbox per effettuare la ricerca su tutto il territorio nazionale, iterando automaticamente sulle diverse regioni o aree.
- **Progresso in Tempo Reale**: Una barra di avanzamento dinamica mostra lo stato del processo di scraping in tempo reale.
- **Esportazione in CSV**: I dati raccolti vengono salvati automaticamente in un file `.csv` con un nome che include paese, attività, località e data.
- **Rimozione Duplicati**: Un processo automatico pulisce il file CSV finale per rimuovere eventuali contatti duplicati.
- **Performance Ottimizzata**: Sfrutta tecniche di programmazione asincrona (`asyncio`) e multithreading per velocizzare la raccolta dati, specialmente per gli scraper di Germania e Svizzera.

## 🛠️ Scraper Disponibili

| Icona | Paese | Directory di Origine | Metodo di Scraping |
|:---:|:---|:---|:---|
| 🍕 | **Italia** | `PagineGialle.it` | Scansione di un endpoint JSON pagina per pagina. |
| 🍺 | **Germania**| `GelbeSeiten.de` | Richieste asincrone per raccogliere i link delle attività e successiva estrazione delle email. |
| 🍫 | **Svizzera**| `local.ch` | Estrazione dei dati da un oggetto JSON (`__NEXT_DATA__`) e scraping parallelo delle pagine con ThreadPoolExecutor. |

## 🚀 Installazione

Per eseguire il progetto in locale, segui questi passaggi:

1.  **Clona la repository**
    ```sh
    git clone [https://github.com/pcbisgood/BSscraper.git)
    cd BSscraper
    ```

2.  **Crea un ambiente virtuale (consigliato)**
    ```sh
    python -m venv venv
    source venv/bin/activate  # Su Windows: venv\Scripts\activate
    ```

3.  **Installa le dipendenze**
    ```sh
    pip install -r requirements.txt
    ```

## 🏃 Esecuzione

Una volta installate le dipendenze, avvia l'applicazione eseguendo il file `main.py`:

```sh
python main.py
Come usare l'applicazione:
Seleziona il paese target cliccando sull'icona corrispondente (🍕, 🍺, o 🍫).

Clicca su "Next".

Premi "Add Row" per aggiungere una o più righe di ricerca.

Nella colonna "Attivita", inserisci il tipo di attività che vuoi cercare.

Nella colonna "Dove", inserisci la città o la regione.

Nota: Se vuoi cercare su tutto il territorio nazionale, spunta la casella "Tutto il Territorio". La colonna "Dove" verrà disabilitata.

Clicca su "Start" per avviare il processo di scraping.

Al termine, una notifica confermerà che il processo è finito e il file CSV è stato salvato nella cartella CSV/.

Utility Aggiuntiva
Nella repository è presente lo script counter.py, che può essere usato per analizzare rapidamente un file CSV generato. Conta e stampa il numero totale di contatti telefonici, numeri WhatsApp ed email trovati.
