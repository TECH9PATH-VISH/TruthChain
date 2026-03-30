import hashlib
import os
from web3 import Web3
from web3.exceptions import ContractLogicError

try:
    import streamlit as st
    CONTRACT_ADDRESS = st.secrets.get("CONTRACT_ADDRESS", "")
    PRIVATE_KEY      = st.secrets.get("PRIVATE_KEY", "")
    RPC_URL          = st.secrets.get("RPC_URL", "http://127.0.0.1:7545")
except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")
    PRIVATE_KEY      = os.getenv("PRIVATE_KEY", "")
    RPC_URL          = os.getenv("RPC_URL", "http://127.0.0.1:7545")

if not CONTRACT_ADDRESS:
    raise EnvironmentError("CONTRACT_ADDRESS is not set.")
if not PRIVATE_KEY:
    raise EnvironmentError("PRIVATE_KEY is not set.")

w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    raise ConnectionError(f"Cannot reach blockchain node at {RPC_URL}.")

SENDER_ADDRESS = w3.eth.account.from_key(PRIVATE_KEY).address

CONTRACT_ABI = [
    {"anonymous": False, "inputs": [{"indexed": True, "internalType": "bytes32", "name": "textHash", "type": "bytes32"}, {"indexed": False, "internalType": "uint8", "name": "credibilityScore", "type": "uint8"}, {"indexed": False, "internalType": "string", "name": "label", "type": "string"}, {"indexed": True, "internalType": "address", "name": "submitter", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}], "name": "RecordAdded", "type": "event"},
    {"inputs": [{"internalType": "bytes32", "name": "_textHash", "type": "bytes32"}, {"internalType": "uint8", "name": "_score", "type": "uint8"}, {"internalType": "string", "name": "_label", "type": "string"}], "name": "recordNews", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "bytes32", "name": "_textHash", "type": "bytes32"}], "name": "getRecord", "outputs": [{"components": [{"internalType": "bytes32", "name": "textHash", "type": "bytes32"}, {"internalType": "uint8", "name": "credibilityScore", "type": "uint8"}, {"internalType": "string", "name": "label", "type": "string"}, {"internalType": "address", "name": "submitter", "type": "address"}, {"internalType": "uint256", "name": "timestamp", "type": "uint256"}, {"internalType": "bool", "name": "exists", "type": "bool"}], "internalType": "struct NewsRegistry.NewsRecord", "name": "", "type": "tuple"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "bytes32", "name": "_textHash", "type": "bytes32"}], "name": "hashExists", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "totalRecords", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
]

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=CONTRACT_ABI,
)

def _text_to_bytes32(text: str) -> bytes:
    return hashlib.sha256(text.encode("utf-8")).digest()

def check_hash_exists(text: str) -> dict:
    text_hash_bytes = _text_to_bytes32(text)
    exists = contract.functions.hashExists(text_hash_bytes).call()
    return {"exists": exists, "article_hash": "0x" + text_hash_bytes.hex()}

def analyze_and_record(article_text: str) -> dict:
    if not isinstance(article_text, str) or not article_text.strip():
        raise ValueError("article_text must be a non-empty string.")

    text_hash_bytes = _text_to_bytes32(article_text)
    text_hash_hex   = "0x" + text_hash_bytes.hex()

    if contract.functions.hashExists(text_hash_bytes).call():
        record = contract.functions.getRecord(text_hash_bytes).call()
        return {
            "already_verified": True,
            "article_hash":     text_hash_hex,
            "label":            record[2],
            "raw_score":        record[1],
            "confidence":       record[1] / 100,
            "tx_hash":          None,
            "block_number":     None,
            "timestamp":        record[4],
        }

    from detector import get_credibility
    credibility = get_credibility(article_text)
    label       = str(credibility["label"])
    raw_score   = credibility["raw_score"]
    clean_score = max(0, min(100, int(float(raw_score))))

    nonce = w3.eth.get_transaction_count(SENDER_ADDRESS)
    txn = contract.functions.recordNews(
        text_hash_bytes,
        clean_score,
        label,
    ).build_transaction({
        "from":     SENDER_ADDRESS,
        "nonce":    nonce,
        "gas":      300_000,
        "gasPrice": w3.eth.gas_price,
    })

    signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
    tx_hash    = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    receipt    = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status != 1:
        raise ContractLogicError(f"Transaction reverted. Hash: {tx_hash.hex()}")

    return {
        "already_verified": False,
        "article_hash":     text_hash_hex,
        "label":            label,
        "raw_score":        raw_score,
        "confidence":       credibility["confidence"],
        "tx_hash":          receipt.transactionHash.hex(),
        "block_number":     receipt.blockNumber,
        "timestamp":        None,
    }
