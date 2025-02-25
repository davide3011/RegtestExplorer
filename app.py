from flask import Flask, render_template, request, redirect, url_for, flash
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import re, logging
from logging.handlers import RotatingFileHandler
import os
if not os.path.exists('logs'):
    os.makedirs('logs')

app = Flask(__name__)
app.secret_key = 'sostituisci_con_una_chiave_sicura'

# Configurazione RPC (modifica secondo le configurazioni del 'bitcoin.conf')
RPC_USER = 'RPC_USER'
RPC_PASSWORD = 'RPC_PASSWORD'
RPC_ADDRESS = 'IP_ADDRESS'
RPC_PORT = 8332

def get_rpc_connection():
    url = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_ADDRESS}:{RPC_PORT}"
    return AuthServiceProxy(url)

def is_numeric(s):
    return s.isdigit()

def is_hash(s):
    # Se è esattamente 64 caratteri e non corrisponde a nessun pattern di indirizzo, allora è un hash.
    if len(s) != 64:
        return False
    # Controlla che la stringa sia esadecimale
    if re.match(r'^[0-9a-fA-F]{64}$', s) is None:
        return False
    # Nessun indirizzo Bitcoin ha 64 caratteri; se arrivi qui, è un hash
    return True

def is_address(s):
    # Controlla indirizzi legacy: iniziano con 1, 3, m, n o 2
    legacy = re.match(r'^[13mn2][a-zA-Z0-9]{25,34}$', s)
    if legacy:
        return True
    # Controlla indirizzi bech32: per mainnet (bc1), testnet (tb1) e regtest (bcrt1)
    bech32 = re.match(r'^(bc1|[tb]crt1)[a-z0-9]{6,90}$', s)
    return bech32 is not None

# Filtro Jinja per formattare i numeri in formato decimale (8 cifre decimali)
@app.template_filter('fnum')
def fnum(value):
    try:
        return "{:.8f}".format(float(value))
    except Exception:
        return value

@app.route('/')
def index():
    rpc = get_rpc_connection()
    try:
        blockchain_info = rpc.getblockchaininfo()
        chain = blockchain_info.get("chain")
        blocks = blockchain_info.get("blocks")
        bestblockhash = blockchain_info.get("bestblockhash")
        difficulty = blockchain_info.get("difficulty")
        mediantime = blockchain_info.get("mediantime")
        size_on_disk = blockchain_info.get("size_on_disk")
        
        # Ottieni il "time" del best block
        bestblock = rpc.getblock(bestblockhash)
        time_value = bestblock.get("time")
        
        # Ottieni informazioni sullo stato UTXO (bitcoin circolanti)
        txoutset_info = rpc.gettxoutsetinfo()
        circulating_total = txoutset_info.get("total_amount")
        txout_transactions = txoutset_info.get("transactions")
        
        # Recupera gli ultimi 5 blocchi
        last_blocks = []
        current_height = blocks
        start_height = max(0, current_height - 4)
        for h in range(start_height, current_height + 1):
            block_hash = rpc.getblockhash(h)
            block_data = rpc.getblock(block_hash)
            last_blocks.append({
                "height": block_data["height"],
                "hash": block_data["hash"],
                "time": block_data["time"]
            })
        last_blocks = sorted(last_blocks, key=lambda x: x["height"], reverse=True)
        
        return render_template('index.html', 
                               chain=chain,
                               blocks=blocks,
                               bestblockhash=bestblockhash,
                               difficulty=difficulty,
                               time_value=time_value,
                               mediantime=mediantime,
                               size_on_disk=size_on_disk,
                               circulating_total=circulating_total,
                               txout_transactions=txout_transactions,
                               last_blocks=last_blocks)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        flash("Inserisci una query di ricerca.")
        return redirect(url_for('index'))

    if is_numeric(q):
        # Tratta la query come altezza di blocco
        return redirect(url_for('block', identifier=q))
    elif is_address(q):
        # Se corrisponde al formato di un indirizzo, reindirizza a quella rotta
        return redirect(url_for('address', address=q))
    elif len(q) == 64 and re.match(r'^[0-9a-fA-F]{64}$', q):
        # Se è un hash (txid o block hash)
        rpc = get_rpc_connection()
        try:
            # Prova a usare getblock; se riesce, è un blocco
            block = rpc.getblock(q, 2)
            if block:
                return redirect(url_for('block', identifier=q))
        except Exception:
            # Se getblock lancia un'eccezione (ad es. perché il txid non è un blocco),
            # reindirizza alla rotta per le transazioni
            pass
        return redirect(url_for('transaction', txid=q))
    else:
        flash("Query non riconosciuta.")
        return redirect(url_for('index'))

@app.route('/block/<identifier>')
def block(identifier):
    rpc = get_rpc_connection()
    try:
        # Se l'identificatore è numerico, ricava il block hash dall'altezza
        if is_numeric(identifier):
            block_hash = rpc.getblockhash(int(identifier))
        else:
            block_hash = identifier
        # Ottieni il blocco con verbose=2 (dati completi)
        block_data = rpc.getblock(block_hash, 2)
        
        # Estrai le informazioni generali
        general_info = {
            "hash": block_data.get("hash"),
            "confirmations": block_data.get("confirmations"),
            "height": block_data.get("height"),
            "version": block_data.get("version"),
            "versionHex": block_data.get("versionHex"),
            "merkleroot": block_data.get("merkleroot"),
            "time": block_data.get("time"),
            "mediantime": block_data.get("mediantime"),
            "nonce": block_data.get("nonce"),
            "bits": block_data.get("bits"),
            "difficulty": block_data.get("difficulty"),
            "chainwork": block_data.get("chainwork"),
            "nTx": block_data.get("nTx"),
            "previousblockhash": block_data.get("previousblockhash"),
            "nextblockhash": block_data.get("nextblockhash", None),
            "strippedsize": block_data.get("strippedsize"),
            "size": block_data.get("size"),
            "weight": block_data.get("weight")
        }
        
        # Le transazioni del blocco: il primo è la coinbase, gli altri normali
        txs = block_data.get("tx", [])
        coinbase_tx = None
        normal_txs = []
        if txs:
            coinbase_tx = txs[0]
            for tx in txs[1:]:
                summary_tx = {
                    "txid": tx.get("txid"),
                    "size": tx.get("size"),
                    "vsize": tx.get("vsize"),
                    "weight": tx.get("weight"),
                    "locktime": tx.get("locktime")
                }
                normal_txs.append(summary_tx)
        
        return render_template("block.html", general_info=general_info, coinbase_tx=coinbase_tx, normal_txs=normal_txs)
    except JSONRPCException as e:
        return render_template("error.html", error=str(e))
    except Exception as ex:
        return render_template("error.html", error=str(ex))

@app.route('/tx/<txid>')
def transaction(txid):
    rpc = get_rpc_connection()
    try:
        # Usa sempre getrawtransaction con verbose=True per ottenere il JSON completo dalla blockchain
        tx = rpc.getrawtransaction(txid, True)
        
        # Prepara i dati generali della transazione
        tx_info = {
            "hex": tx.get("hex"),
            "txid": tx.get("txid"),
            "hash": tx.get("hash"),
            "size": tx.get("size"),
            "vsize": tx.get("vsize"),
            "weight": tx.get("weight"),
            "version": tx.get("version"),
            "locktime": tx.get("locktime")
        }
        
        # Calcola la fee: somma degli input (escludendo eventuali coinbase) meno la somma degli output
        total_in = 0.0
        for vin in tx.get("vin", []):
            if "coinbase" in vin:
                continue
            prev_tx = rpc.getrawtransaction(vin["txid"], True)
            prev_vout = prev_tx["vout"][vin["vout"]]
            total_in += float(prev_vout.get("value", 0))
        total_out = sum(float(vout.get("value", 0)) for vout in tx.get("vout", []))
        fee = total_in - total_out if total_in > 0 else 0.0
        
        # Determina se la transazione è coinbase
        is_coinbase = any("coinbase" in vin for vin in tx.get("vin", []))
        
        if is_coinbase:
            sender = None
            recipients = []
            # Filtra gli output di tipo "nulldata"
            for v in tx.get("vout", []):
                spk_v = v.get("scriptPubKey", {})
                if spk_v.get("type") == "nulldata":
                    continue
                recipient = {
                    "address": spk_v.get("address") or (spk_v.get("addresses", [None])[0]),
                    "value": v.get("value", 0)
                }
                recipients.append(recipient)
        else:
            vouts = tx.get("vout", [])
            if len(vouts) > 0:
                first_vout = vouts[0]
                spk = first_vout.get("scriptPubKey", {})
                sender = {
                    "address": spk.get("address") or (spk.get("addresses", [None])[0]),
                    "asm": spk.get("asm"),
                    "hex": spk.get("hex"),
                    "type": spk.get("type"),
                    "value": first_vout.get("value", 0)
                }
                recipients = []
                for v in vouts[1:]:
                    spk_v = v.get("scriptPubKey", {})
                    recipient = {
                        "address": spk_v.get("address") or (spk_v.get("addresses", [None])[0]),
                        "value": v.get("value", 0)
                    }
                    recipients.append(recipient)
        
        return render_template("transaction.html", tx_info=tx_info, sender=sender, 
                               recipients=recipients, fee=fee, is_coinbase=is_coinbase)
    except JSONRPCException as e:
        return render_template("error.html", error=str(e))
    except Exception as ex:
        return render_template("error.html", error=str(ex))

@app.route('/address/<address>')
def address(address):
    rpc = get_rpc_connection()
    try:
        try:
            # Importa l'indirizzo se non è già presente
            rpc.importaddress(address, "", True)
        except JSONRPCException:
            pass
        
        # Esegui lo scan degli UTXO per l'indirizzo
        scan_result = rpc.scantxoutset("start", [f"addr({address})"])
        if scan_result and scan_result.get("success", False):
            total_amount = scan_result.get("total_amount", 0)
            unspents = scan_result.get("unspents", [])
            height = scan_result.get("height")
            
            # Per ottenere la cronologia delle transazioni, usiamo listtransactions
            transactions = rpc.listtransactions("*", 100, 0, True)
            tx_history = [tx for tx in transactions if tx.get("address", "").lower() == address.lower()]
            
            return render_template("address.html",
                                   address=address,
                                   total_amount=total_amount,
                                   unspents=unspents,
                                   height=height,
                                   tx_history=tx_history)
        else:
            flash("Nessun UTXO trovato per questo indirizzo.")
            return redirect(url_for('index'))
    except JSONRPCException as e:
        return render_template("error.html", error=str(e))
    except Exception as ex:
        return render_template("error.html", error=str(ex))

if __name__ == '__main__':
    # Usa FileHandler per scrivere sempre sullo stesso file
    file_handler = logging.FileHandler('logs/explorer.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    
    # Aggiungi lo stesso handler al logger di Werkzeug per loggare le richieste HTTP
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.addHandler(file_handler)
    werkzeug_logger.setLevel(logging.INFO)
    
    app.logger.info("Explorer avviato")
    
    # Avvia l'app senza reloader per evitare doppie inizializzazioni
    app.run(debug=True, use_reloader=False)
