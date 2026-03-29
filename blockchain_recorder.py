"""
blockchain_recorder.py — TruthChain
Hashes article text, calls the AI detector, and records results on-chain
via a local Ganache node.
"""

import hashlib
import os

from dotenv import load_dotenv
from web3 import Web3
from web3.exceptions import ContractLogicError

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv()

CONTRACT_ADDRESS: str = os.getenv("CONTRACT_ADDRESS", "")
PRIVATE_KEY: str      = os.getenv("PRIVATE_KEY", "")

if not CONTRACT_ADDRESS:
    raise EnvironmentError("CONTRACT_ADDRESS is not set in your .env file.")
if not PRIVATE_KEY:
    raise EnvironmentError("PRIVATE_KEY is not set in your .env file.")

# ---------------------------------------------------------------------------
# Web3 / Ganache connection
# ---------------------------------------------------------------------------

GANACHE_RPC = "http://127.0.0.1:7545"

w3 = Web3(Web3.HTTPProvider(GANACHE_RPC))

if not w3.is_connected():
    raise ConnectionError(
        f"Cannot reach Ganache at {GANACHE_RPC}. "
        "Make sure Ganache is running before importing this module."
    )

# Derive the sender address from the private key
SENDER_ADDRESS: str = w3.eth.account.from_key(PRIVATE_KEY).address

# ---------------------------------------------------------------------------
# Minimal ABI — only the functions TruthChain actually calls
# ---------------------------------------------------------------------------
# Expected smart-contract interface:
#
#   function hashExists(bytes32 articleHash) external view returns (bool);
#
#   function recordNews(
#       bytes32 articleHash,
#       string  calldata label,      // "FAKE" | "REAL"
#       uint256 rawScore             // credibility * 1e6, stored as uint
#   ) external;
#
#   function getRecord(bytes32 articleHash)
#       external view
#       returns (string memory label, uint256 rawScore, uint256 timestamp);

CONTRACT_ABI = [
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"internalType": "bytes32",
				"name": "textHash",
				"type": "bytes32"
			},
			{
				"indexed": False,
				"internalType": "uint8",
				"name": "credibilityScore",
				"type": "uint8"
			},
			{
				"indexed": False,
				"internalType": "string",
				"name": "label",
				"type": "string"
			},
			{
				"indexed": True,
				"internalType": "address",
				"name": "submitter",
				"type": "address"
			},
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			}
		],
		"name": "RecordAdded",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "bytes32",
				"name": "_textHash",
				"type": "bytes32"
			},
			{
				"internalType": "uint8",
				"name": "_score",
				"type": "uint8"
			},
			{
				"internalType": "string",
				"name": "_label",
				"type": "string"
			}
		],
		"name": "recordNews",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "bytes32",
				"name": "_textHash",
				"type": "bytes32"
			}
		],
		"name": "getRecord",
		"outputs": [
			{
				"components": [
					{
						"internalType": "bytes32",
						"name": "textHash",
						"type": "bytes32"
					},
					{
						"internalType": "uint8",
						"name": "credibilityScore",
						"type": "uint8"
					},
					{
						"internalType": "string",
						"name": "label",
						"type": "string"
					},
					{
						"internalType": "address",
						"name": "submitter",
						"type": "address"
					},
					{
						"internalType": "uint256",
						"name": "timestamp",
						"type": "uint256"
					},
					{
						"internalType": "bool",
						"name": "exists",
						"type": "bool"
					}
				],
				"internalType": "struct NewsRegistry.NewsRecord",
				"name": "",
				"type": "tuple"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "bytes32",
				"name": "_textHash",
				"type": "bytes32"
			}
		],
		"name": "hashExists",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "bytes32",
				"name": "",
				"type": "bytes32"
			}
		],
		"name": "records",
		"outputs": [
			{
				"internalType": "bytes32",
				"name": "textHash",
				"type": "bytes32"
			},
			{
				"internalType": "uint8",
				"name": "credibilityScore",
				"type": "uint8"
			},
			{
				"internalType": "string",
				"name": "label",
				"type": "string"
			},
			{
				"internalType": "address",
				"name": "submitter",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			},
			{
				"internalType": "bool",
				"name": "exists",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "totalRecords",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=CONTRACT_ABI,
)


# ---------------------------------------------------------------------------
# 1. Hashing — character-sensitive, no normalisation
# ---------------------------------------------------------------------------

def hash_article_hex(text: str) -> str:
    """Return the SHA-256 hex digest of *text*.

    Deliberately does NOT call ``.lower()`` or ``.strip()`` so the hash
    is sensitive to every character, including whitespace and casing.

    Returns
    -------
    str
        64-character lowercase hex string (256 bits).
    """
    if not isinstance(text, str):
        raise TypeError("`text` must be a plain string.")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hex_to_bytes32(hex_digest: str) -> bytes:
    """Convert a 64-char hex string to a 32-byte ``bytes`` value for the ABI."""
    return bytes.fromhex(hex_digest)


# ---------------------------------------------------------------------------
# 2. UI helper — check existence without side-effects
# ---------------------------------------------------------------------------

def check_hash_exists(text: str) -> dict:
    """Check whether *text* has already been recorded on-chain.

    Intended for the UI layer so it can show 'Already Verified' without
    triggering a full analysis.

    Parameters
    ----------
    text : str
        Raw article text (not pre-hashed).

    Returns
    -------
    dict
        {
            "exists":      bool,
            "article_hash": str,   # 64-char hex
        }
    """
    hex_digest   = hash_article_hex(text)
    article_hash = _hex_to_bytes32(hex_digest)

    exists: bool = contract.functions.hashExists(article_hash).call()

    return {
        "exists":       exists,
        "article_hash": hex_digest,
    }
load_dotenv()

# Helper 1: This establishes the "Phone Line" to Ganache
def connect_to_blockchain():
    rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:7545")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise ConnectionError(f"❌ Could not connect to Ganache at {rpc_url}")
    return w3

# Helper 2: This identifies your "Smart Contract" on the ledger
def get_contract_instance(w3):
    address = os.getenv("CONTRACT_ADDRESS")
    # This ABI must match your NewsRegistry.sol exactly
    abi = [
        {"inputs": [{"internalType": "bytes32", "name": "_textHash", "type": "bytes32"}, {"internalType": "uint8", "name": "_score", "type": "uint8"}, {"internalType": "string", "name": "_label", "type": "string"}], "name": "recordNews", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
        {"inputs": [{"internalType": "bytes32", "name": "_textHash", "type": "bytes32"}], "name": "getRecord", "outputs": [{"components": [{"internalType": "bytes32", "name": "textHash", "type": "bytes32"}, {"internalType": "uint8", "name": "credibilityScore", "type": "uint8"}, {"internalType": "string", "name": "label", "type": "string"}, {"internalType": "address", "name": "submitter", "type": "address"}, {"internalType": "uint256", "name": "timestamp", "type": "uint256"}, {"internalType": "bool", "name": "exists", "type": "bool"}], "internalType": "struct NewsRegistry.NewsRecord", "name": "", "type": "tuple"}], "stateMutability": "view", "type": "function"},
        {"inputs": [{"internalType": "bytes32", "name": "_textHash", "type": "bytes32"}], "name": "hashExists", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"}
    ]
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)

# Helper 3: This is needed for the 'Already Verified' check in your UI
def check_hash_exists(text: str):
    w3 = connect_to_blockchain()
    contract = get_contract_instance(w3)
    text_hash_bytes = hashlib.sha256(text.encode('utf-8')).digest()
    exists = contract.functions.hashExists(text_hash_bytes).call()
    return {"exists": exists, "article_hash": "0x" + text_hash_bytes.hex()}


# ---------------------------------------------------------------------------
# 3. Core workflow
# ---------------------------------------------------------------------------

def analyze_and_record(article_text: str):
    """
    Analyzes news with AI and records it to the blockchain.
    Fixed order: (Hash, Score, Label)
    """
    from detector import get_credibility
    
    # 1. Setup Connection
    w3 = connect_to_blockchain()
    contract = get_contract_instance(w3)
    
    # 2. Hashing
    text_hash_bytes = hashlib.sha256(article_text.encode('utf-8')).digest()
    text_hash_hex = "0x" + text_hash_bytes.hex()

    # 3. Check for duplicates
    if contract.functions.hashExists(text_hash_bytes).call():
        record = contract.functions.getRecord(text_hash_bytes).call()
        # Mapping the tuple return from Solidity back to a dictionary
        return {
            "success": False, 
            "label": record[2], 
            "raw_score": record[1], 
            "timestamp": record[4],
            "text_hash": text_hash_hex
        }

    ## ... inside analyze_and_record ...
    
    # 4. Get AI Score
    det = get_credibility(article_text)
    
    # We store the 'Real' percentage as the score.
    # If the AI says 95% REAL, we store 95.
    # If the AI says 5% REAL (meaning 95% FAKE), we store 5.
    clean_score = int(float(det['raw_score']))

    # (Hash [bytes32], Score [uint8], Label [string])
    txn = contract.functions.recordNews(
        text_hash_bytes, 
        clean_score, 
        str(det['label']) 
    ).build_transaction({
        # ... rest of transaction code ...
    })

    # 6. Sign and Send
    signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    return {
        "success": True, 
        "tx_hash": tx_hash.hex(), 
        "block_number": receipt.blockNumber, 
        "text_hash": text_hash_hex,
        "label": det['label'],
        "raw_score": clean_score
    }


# ---------------------------------------------------------------------------
# Smoke-test (run directly: python blockchain_recorder.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample = (
        "Scientists have discovered a new species of deep-sea fish "
        "that can produce its own light without any symbiotic bacteria."
    )

    print(f"Sender  : {SENDER_ADDRESS}")
    print(f"Contract: {CONTRACT_ADDRESS}")
    print(f"Hash    : {hash_article_hex(sample)}")
    print()

    existence = check_hash_exists(sample)
    print(f"check_hash_exists → exists={existence['exists']}")
    print()

    result = analyze_and_record(sample)
    for key, value in result.items():
        print(f"  {key:<20}: {value}")