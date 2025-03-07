# Blockchain Explorer

Blockchain Explorer è un’applicazione web sviluppata in Python con Flask che consente di navigare e visualizzare i dati della blockchain Bitcoin.

L’app utilizza le API RPC del nodo Bitcoin per recuperare informazioni sulla rete, sui blocchi, sulle transazioni e sugli indirizzi e le presenta in maniera strutturata tramite template HTML con Jinja2 e uno style CSS personalizzato.

## Funzionalità Principali

### Homepage (index.html)

- **Informazioni di Rete:** Visualizza dati ottenuti tramite la chiamata RPC `getblockchaininfo`, quali:
  - **Chain:** Tipo di rete (es. regtest).
  - **Blocks:** Numero totale di blocchi.
  - **Best Block Hash:** Hash del blocco più recente (cliccabile per approfondimenti).
  - **Difficulty:** Difficoltà attuale (visualizzata come intero).
  - **Time & Median Time:** Timestamp e tempo mediano (in formato UNIX Epoch).
  - **Size on Disk:** Dimensione occupata dal nodo sul disco.
  - **Circulating Supply:** Importo totale dei bitcoin circolanti (ottenuto con `gettxoutsetinfo`).
  - **Total Transactions:** Numero totale di transazioni UTXO.
- **Ultimi 10 Blocchi:** Elenca in una tabella gli ultimi 10 blocchi con altezza, hash (cliccabile), timestamp e numero di transazioni.


### Pagina Blocco (block.html):

- Recupera i dati completi del blocco tramite la chiamata `getblock <hash> 2`.
- Mostra una sezione di **informazioni generali** (hash, conferme, altezza, versioni, merkleroot, tempi, nonce, bits, difficulty, chainwork, numero di transazioni, dimensioni e peso).
- La **transazione coinbase** (il primo elemento del blocco) viene presentata in un "sottoblocco" con informazioni chiave (txid, importo e indirizzo di ricezione, con link all’indirizzo).
- Le **altre transazioni** vengono riassunte in una tabella con i dati principali (txid, virtual size, weight e fee).

### Pagina Transazione (transaction.html):

- Recupera i dettagli della transazione con `getrawtransaction <txid> true`.
- Mostra una sezione con le **informazioni generali** (hex, txid, hash, dimensioni, peso, version, locktime e fee).
- Presenta due sezioni separate per:
  - **Input:** Per ogni input, visualizza txid (cliccabile se non coinbase), vout, sequence e lo scriptSig (in formato asm).
  - **Output:** Per ogni output, visualizza indice, valore (in BTC), indirizzo (se disponibile, cliccabile) e tipo.

### Pagina Indirizzo (address.html):

- Utilizza la chiamata `scantxoutset "start" '["addr(<indirizzo>)"]'` per ottenere il saldo e gli UTXO relativi all’indirizzo.
- La pagina è divisa in due blocchi:
  - **Informazioni Generali:** Mostra l’indirizzo, il numero di txouts, l’altezza di scan, il best block e il totale UTXO.
  - **Transazioni (UTXO):** Per ogni UTXO (transazione), vengono mostrate informazioni come txid, vout, scriptPubKey/descrizione, importo, flag coinbase, altezza, blockhash e conferme.

## Struttura dei file

- **app.py:** Il file principale del backend, che definisce le rotte dell’app e gestisce le chiamate RPC al nodo Bitcoin.
- **rpc_connection.py:** Contiene la funzione `get_rpc_connection()` per stabilire la connessione RPC, configurata con le credenziali e la porta del nodo Bitcoin.
- **templates/**
  - **base.html:** Il layout base (header, footer, container).
  - **index.html:** Template della homepage.
  - **block.html:** Template per visualizzare i dettagli di un blocco.
  - **transaction.html:** Template per visualizzare i dettagli di una transazione (con sezioni separate per informazioni generali, input e output).
  - **address.html:** Template per la visualizzazione dei dettagli di un indirizzo (diviso in blocchi per informazioni generali e UTXO).
  - **error.html:** Template per la visualizzazione degli errori.
- **static/style.css:** Il file CSS che definisce le variabili di stile e la formattazione per tutti i template.  
  In questa versione, lo style è uniformato utilizzando solo due colori principali (primary e secondary) per garantire coerenza nel layout.

## Configurazione del Bitcoin Node

Per utilizzare l’explorer, il tuo nodo Bitcoin deve essere configurato per abilitare le chiamate RPC. Ecco un esempio di configurazione per il file `bitcoin.conf`:

```ini
# Abilita il server RPC
server=1

# Imposta le credenziali RPC (devono corrispondere a quelle impostate in rpc_connection.py)
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

Per utilizzare l'applicazione, è necessario avere installato Python 3.x e Bitcoin Core (o un altro nodo compatibile). Assicurati di avere già installato il package manager pip.

### 2. Installazione

Clona il repository e installa i pacchetti necessari: apri il terminale, posizionati nella cartella del progetto e installa tutte le dipendenze eseguendo il comando:

```bash
pip install -r requirements.txt
```

### 3. Configurazione

- Aggiorna le credenziali RPC in [```rpc_connection.py```](rpc_connection.py) (RPC_USER, RPC_PASSWORD, RPC_ADDRESS e RPC_PORT).
- Configura il tuo nodo Bitcoin come indicato sopra e avvialo.

### 4. Avvio dell'explorer

Dalla directory del progetto, esegui:

```bash
python app.py
```

Apri il browser e vai all'indirizzo http://localhost:5000 per iniziare a utilizzare l'explorer.

## Note

- Questa applicazione è attualmente configurata per lavorare in modalità regtest, ma può essere facilmente adattata per testnet o mainnet modificando le impostazioni RPC e la configurazione del nodo.
- Le chiamate sperimentali (come scantxoutset) potrebbero subire modifiche in future versioni di Bitcoin Core.

## Licenza
Questo progetto è distribuito sotto la Licenza MIT.

Vedi il file [LICENSE](LICENSE) per maggiori dettagli.