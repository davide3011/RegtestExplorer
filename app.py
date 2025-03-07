from flask import Flask, render_template, request, redirect, url_for, flash
from rpc_connection import get_rpc_connection
from bitcoinrpc.authproxy import JSONRPCException
import re

app = Flask(__name__)
app.secret_key = 'sostituisci_con_una_chiave_sicura'

# Funzioni di utilità per validare l'input
def is_numeric(s):
    return s.isdigit()

def is_hash(s):
    if len(s) != 64:
        return False
    if re.match(r'^[0-9a-fA-F]{64}$', s) is None:
        return False
    return True

def is_address(s):
    legacy = re.match(r'^[13mn2][a-zA-Z0-9]{25,34}$', s)
    if legacy:
        return True
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
        difficulty = blockchain_info.get("difficulty") # nel template da visualizzare come intero
        mediantime = blockchain_info.get("mediantime")
        size_on_disk = blockchain_info.get("size_on_disk")
        
        # Ottieni il "time" del best block
        bestblock = rpc.getblock(bestblockhash)
        time_value = bestblock.get("time")
        
        # Ottieni informazioni sullo stato UTXO (bitcoin circolanti)
        txoutset_info = rpc.gettxoutsetinfo()
        circulating_total = txoutset_info.get("total_amount")
        txout_transactions = txoutset_info.get("transactions")
        
        # Recupera gli ultimi 10 blocchi
        last_blocks = []
        current_height = blocks
        start_height = max(0, current_height - 9)
        for h in range(start_height, current_height + 1):
            block_hash = rpc.getblockhash(h)
            block_data = rpc.getblock(block_hash)
            last_blocks.append({
                "height": block_data["height"],
                "hash": block_data["hash"],
                "time": block_data["time"],
                "nTx": block_data["nTx"]
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
        if is_numeric(identifier):
            block_hash = rpc.getblockhash(int(identifier))
        else:
            block_hash = identifier
        block_data = rpc.getblock(block_hash, 2)
        
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

        txs = block_data.get("tx", [])
        coinbase_info = {}
        normal_txs = []
        
        if txs:
            # Estrai la coinbase creando una struttura specifica
            coinbase = txs[0]

            coinbase_info = {
                "txid": coinbase.get("txid"),
                # Prendi il valore del primo output, se presente
                "value": coinbase.get("vout")[0].get("value") if coinbase.get("vout") else None,
                # Prendi l'indirizzo dal primo output, verificando se è in "address" o in "addresses"
                "address": coinbase.get("vout")[0].get("scriptPubKey", {}).get("address") if coinbase.get("vout") else None
            }
            # Per le transazioni normali, estrai solo i campi utili
            for tx in txs[1:]:
                # Calcola il totale degli input della transazione
                total_in = 0.0
                for vin in tx.get("vin", []):
                    # Recupera la transazione precedente per ottenere il valore dell'output utilizzato da questo input
                    prev_tx = rpc.getrawtransaction(vin["txid"], True)
                    prev_vout = prev_tx["vout"][vin["vout"]]
                    total_in += float(prev_vout.get("value", 0))
    
                # Calcola il totale degli output della transazione
                total_out = sum(float(vout.get("value", 0)) for vout in tx.get("vout", []))
    
                # La fee è la differenza tra il totale degli input e quello degli output
                fee = total_in - total_out if total_in > 0 else 0.0

                # Crea una struttura specifica per la transazione normale
                tx_info = {
                    "txid": tx.get("txid"),
                    "vsize": tx.get("vsize"),
                    "weight": tx.get("weight"),
                    "fee": fee
                }
                normal_txs.append(tx_info)
 
        return render_template("block.html", general_info=general_info, coinbase_tx=coinbase_info, normal_txs=normal_txs)

    except JSONRPCException as e:
        return render_template("error.html", error=str(e))
    except Exception as ex:
        return render_template("error.html", error=str(ex))

@app.route('/tx/<txid>')
def transaction(txid):
    rpc = get_rpc_connection()
    try:
        tx = rpc.getrawtransaction(txid, True)
        
        # Raggruppa le informazioni generali della transazione
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
        
        # Raggruppa gli input in modo semplificato: per ciascun input, considera txid, vout e sequence
        raw_vin = tx.get("vin", [])
        tx_inputs = []
        for vin in raw_vin:
            if "coinbase" in vin:
                tx_inputs.append({
                    "txid": "Coinbase",
                    "vout": None,
                    "sequence": vin.get("sequence")
                })
            else:
                tx_inputs.append({
                    "txid": vin.get("txid"),
                    "vout": vin.get("vout"),
                    "sequence": vin.get("sequence")
                })
        
        # Raggruppa gli output: per ciascun output, considera value, n e i dettagli dello scriptPubKey
        raw_vout = tx.get("vout", [])
        tx_outputs = []
        for v in raw_vout:
            spk = v.get("scriptPubKey", {})
            tx_outputs.append({
                "value": v.get("value"),
                "n": v.get("n"),
                "scriptPubKey": {
                    "asm": spk.get("asm"),
                    "hex": spk.get("hex"),
                    "address": spk.get("address") if spk.get("address") else (spk.get("addresses")[0] if spk.get("addresses") else None),
                    "type": spk.get("type")
                }
            })
        
        # Calcola la fee solo se la transazione non è coinbase
        if not any("coinbase" in vin for vin in raw_vin):
            total_in = 0.0
            for vin in raw_vin:
                prev_tx = rpc.getrawtransaction(vin["txid"], True)
                prev_vout = prev_tx["vout"][vin["vout"]]
                total_in += float(prev_vout.get("value", 0))
            total_out = sum(float(v.get("value", 0)) for v in raw_vout)
            fee = total_in - total_out if total_in > 0 else 0.0
        else:
            fee = None
        
        return render_template("transaction.html", 
                               tx_info=tx_info, 
                               tx_inputs=tx_inputs, 
                               tx_outputs=tx_outputs,
                               fee=fee, 
                               is_coinbase=any("coinbase" in vin for vin in raw_vin))
    except JSONRPCException as e:
        return render_template("error.html", error=str(e))
    except Exception as ex:
        return render_template("error.html", error=str(ex))

@app.route('/address/<address>')
def address(address):
    rpc = get_rpc_connection()
    try:
        # Costruisci il descriptor come lista Python
        descriptor = [f"addr({address})"]
        scan_result = rpc.scantxoutset("start", descriptor)
        if scan_result and scan_result.get("success", False):
            # Raggruppa le informazioni generali ottenute dalla scansione
            general_info = {
                "txouts": scan_result.get("txouts"),
                "height": scan_result.get("height"),
                "bestblock": scan_result.get("bestblock"),
                "total_amount": scan_result.get("total_amount", 0)
            }
            # La lista delle transazioni (UTXO) si trova in "unspents"
            txs = scan_result.get("unspents", [])
            
            return render_template("address.html",
                                   address=address,
                                   general_info=general_info,
                                   txs=txs)
        else:
            flash("Nessun UTXO trovato per questo indirizzo.")
            return redirect(url_for('index'))
    except Exception as e:
        return render_template("error.html", error=str(e))

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
