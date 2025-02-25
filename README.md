# Blockchain Explorer
Questo progetto è un Blockchain Explorer per reti Bitcoin in modalità regtest (ma facilmente adattabile anche ad altre reti). L'explorer è sviluppato con Python e Flask per il backend, e utilizza HTML, CSS e i template Jinja2 per il frontend.

## Funzionalità Principali

### Homepage (Index)

- Visualizza le informazioni di rete ottenute tramite la chiamata getblockchaininfo:
    - Chain: Il tipo di rete (es. regtest).
    - Blocks: Il numero totale di blocchi.
    - Best Block Hash: L'hash del blocco più recente (cliccabile per visualizzarlo).
    - Difficulty: La difficoltà corrente (formattata in decimale).
    - Time: Il timestamp del blocco migliore (UNIX Epoch).
    - Median Time: Il tempo mediano dei blocchi.
    - Size on Disk: La dimensione occupata sul disco dal nodo.
    - Bitcoin Circolanti: Ottenuti tramite la chiamata gettxoutsetinfo (campo total_amount).
    - Total Transactions: Il numero di transazioni UTXO (campo transactions).
- Elenca gli ultimi 5 blocchi, mostrando per ciascuno altezza, hash (cliccabile) e timestamp.

### Pagina Blocco (block.html):

- Utilizza la chiamata getblock <hash> 2 per recuperare dati completi del blocco.
- Mostra una sezione di informazioni generali sul blocco (hash, conferme, altezza, versioni, merkleroot, tempi, nonce, bits, difficulty, chainwork, dimensione, peso, ecc.).
- Visualizza la transazione coinbase (la prima transazione del blocco) in modo semplificato, mostrando solo txid, importo e l’indirizzo di ricezione (cliccabile per visualizzare le informazioni relative all’indirizzo).
- Riassume le altre transazioni in una tabella con i dati principali (txid, size, virtual size, weight e locktime).

### Pagina Transazione (transaction.html):

- Recupera i dettagli completi della transazione tramite getrawtransaction <txid> true.
- Mostra le informazioni generali (hex, txid, hash, dimensioni, peso, version, locktime e fee).
- Se la transazione non è coinbase, visualizza il “mittente” (primo vout) e i “destinatari” (vout successivi); se è coinbase, visualizza tutti gli output come destinatari.
- I link per txid, indirizzi e block hash sono cliccabili per navigare alle rispettive pagine.

### Pagina Indirizzo (address.html):

- Utilizza la chiamata scantxoutset start ```'["addr(<address>)"]'``` per ottenere il saldo e gli UTXO dell’indirizzo.
- Mostra il saldo totale, l’altezza dello scan e una tabella con gli UTXO disponibili (txid, importo, blockhash, ecc.) in cui txid e blockhash sono link cliccabili.
- Mostra anche la cronologia delle transazioni relative all’indirizzo, con txid, importo e blockhash (cliccabili).

## Come Funziona il Backend
Il backend è gestito da Flask (in app.py), che espone diverse rotte:

- ```/``` - La homepage, che utilizza RPC per ottenere informazioni di rete e gli ultimi 5 blocchi.
- ```/search``` - Analizza la query inserita nella barra di ricerca e reindirizza alla pagina corretta (blocco, transazione o indirizzo) basandosi su una logica di validazione:
    - Se la stringa è numerica, la tratta come altezza di blocco.
    - Se la stringa ha 64 caratteri esadecimali, la tratta come txid o block hash.
    - Se non è 64 caratteri, la funzione is_address (aggiornata per riconoscere sia indirizzi legacy sia bech32) determina se è un indirizzo.
- ```/block/<identifier>``` – Recupera i dettagli del blocco tramite getblock <hash> 2 e li passa al template.
- ```/tx/<txid>``` – Recupera i dettagli della transazione tramite getrawtransaction <txid> true, calcola la fee e distingue le transazioni coinbase dalle normali.
- ```/address/<address>``` – Utilizza scantxoutset per ottenere il saldo e gli UTXO dell’indirizzo, e listtransactions per la cronologia.

Le funzioni helper ```is_numeric```, ```is_hash``` e ```is_address``` (con regex aggiornate) garantiscono la corretta discriminazione dei vari tipi di query.

## Come Funziona il Frontend
Il frontend è composto da template HTML (in ```templates/```):

- **base.html**: struttura comune (header, footer, container).
- **index.html**, **block.html**, **transaction.html**, **address.html**, **error.html**: estendono base.html e contengono sezioni per visualizzare i dati ottenuti dal backend.
I template usano classi CSS come ```.detail-row```, ```.detail-label```, ```.detail-value``` per una presentazione uniforme e link dinamici per navigare tra le pagine.
Il file **style.css** (in ```static/```) definisce le variabili di colore, le tipografie, la struttura dei contenuti e la responsività.

## Configurazione del Bitcoin Node

Per far funzionare correttamente l'explorer, il nodo Bitcoin deve essere configurato per abilitare l'accesso RPC. Ecco un esempio di configurazione per il file ```bitcoin.conf``` in modalità regtest:

```bash
# Abilita il server RPC
server=1

# Imposta le credenziali RPC (devono corrispondere a quelle impostate in app.py)
rpcuseer=RPC_USER
rpcpassword=RPC_PASSWORD

# Abilita la modalità regtest
regtest=1

# Consenti connessioni RPC da localhost
rpcallowip=127.0.0.1

# Se desideri consentire connessioni da altri dispositivi, usa:
# rpcallowip=0.0.0.0/0 oppure rpcallowip=192.168.1.0/24

# Imposta la porta RPC
rpcport=8332
```

Per semplificare la configurazione di Bitcoin Core, si consiglia di utilizzare un generatore di file di configurazione online. Ad esempio, il
[Bitcoin Core Config Generator](https://jlopp.github.io/bitcoin-core-config-generator/) consente di creare in modo interattivo un file 
bitcoin.conf personalizzato in base alle proprie esigneze. Questo strumento aiuta a evitare errori manuali e garantisce una configurazione ottimale del nodo.

Assicurati che il file ```bitcoin.conf``` si trovi nella cartella di dati del nodo Bitcoin.

## Scaricare Bitcoin Core

Per scaricare Bitcoin Core, visita il sito ufficiale: https://bitcoincore.org/en/download/

## Installazione e Avvio
### 1. Prerequisiti
Assicurati di avere installato Python 3 e il package manager pip. Dunque, installa tutti i pacchetti necessari definiti nel file ```requirements.txt```:

```bash
pip install -r requirements.txt
```

### 2. Configurazione

- Aggiorna app.py con le credenziali corrette del tuo nodo (RPC_USER, RPC_PASSWORD, RPC_ADDRESS, RPC_PORT).
- Configura il file bitcoin.conf come mostrato sopra e avvia il nodo Bitcoin.

### 3. Avvio dell'Explorer
Dalla directory del progetto, esegui:

```bash
python app.py
```

L'applicazione verrà eseguita in modalità debug (modifica per la produzione).

### 4. Navigazione
Apri il browser e vai all'indirizzo http://localhost:5000 per iniziare a utilizzare l'explorer.

## Logging

L'applicazione utilizza il modulo di logging integrato di Python per mantenere uno storico delle attività e delle richieste HTTP. In particolare:

- **RotatingFileHandler:** I log vengono scritti in un file chiamato explorer.log nella directory del progetto. Quando il file raggiunge 10 KB, viene ruotato (vengono mantenuti fino a 10 backup).

- **-Configurazione dei Logger:** Il logger dell’applicazione (app.logger) e quello di Werkzeug (che gestisce le richieste HTTP) sono configurati per registrare messaggi a livello INFO e superiori.

- **Verifica dei Log:** Al momento dell’avvio, viene scritto un messaggio di test ("Explorer avviato") nel file di log. Per monitorare in tempo reale l’attività, puoi usare ad esempio il comando:

```bash
tail -f explorer.log
```

(oppure aprire il file con un editor di testo che supporta il live update).

Ogni richiesta (oltre agli eventi interni dell'app) verrà registrata in explorer.log, consentendoti di avere uno storico completo delle attività.

## Licenza
Questo progetto è distribuito sotto la Licenza MIT.

Vedi il file [LICENSE](LICENSE) per maggiori dettagli.
