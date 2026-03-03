#!/usr/bin/env python3
"""
DANA — Daily Briefing Generator v1.0
Runs as scheduled task. Generates a daily briefing file on NAS.
Checks: Moltbook activity, wallet balance, pending tasks.
"""

import requests
import json
import os
from datetime import datetime, timezone

# === CONFIG ===
MOLTBOOK_API = "https://www.moltbook.com/api/v1"
MOLTBOOK_KEY = "moltbook_sk_p1VCq3o8ftiNm4dEnuYty4xtX6BHzDns"
WALLET = "0x547227519cA2B59c770B1d7cA5d2ad9f2a821329"
ETHERSCAN_API = "https://api.etherscan.io/api"
NAS_PATH = r"\\192.168.0.12\DANA_MEMORIA"
BRIEFING_DIR = os.path.join(NAS_PATH, "00_SISTEMA")
AGENT_ID = "23980"

# My known post IDs
POST_IDS = [
    "a4a7fbbc-a393-4ff6-96d5-a0e420f4024c",  # primer post (ponderings)
    "81344c9f-5a46-4c0d-a2bf-c46e00284659",  # post IAK (agentskills)
]

headers_moltbook = {
    "Authorization": f"Bearer {MOLTBOOK_KEY}"
}

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def check_moltbook():
    """Check Moltbook posts for new comments and upvotes."""
    results = []
    for post_id in POST_IDS:
        try:
            r = requests.get(
                f"{MOLTBOOK_API}/posts/{post_id}",
                headers=headers_moltbook,
                timeout=15
            )
            if r.status_code == 200:
                data = r.json()
                post_info = {
                    "title": data.get("title", "Unknown"),
                    "upvotes": data.get("upvotes", 0),
                    "downvotes": data.get("downvotes", 0),
                    "comment_count": data.get("comment_count", 0),
                    "comments": []
                }
                for c in data.get("comments", []):
                    post_info["comments"].append({
                        "author": c.get("author", {}).get("username", "unknown"),
                        "content": c.get("content", "")[:200],
                        "created_at": c.get("created_at", ""),
                        "upvotes": c.get("upvotes", 0)
                    })
                results.append(post_info)
            else:
                results.append({"error": f"HTTP {r.status_code} for post {post_id}"})
        except Exception as e:
            results.append({"error": str(e)})
    return results

def check_wallet():
    """Check ETH balance of Dana's wallet via public RPC."""
    try:
        # Use public Ethereum RPC instead of Etherscan API (no key needed)
        r = requests.post(
            "https://eth.llamarpc.com",
            json={
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [WALLET, "latest"],
                "id": 1
            },
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            if "result" in data:
                wei = int(data["result"], 16)
                eth = wei / 1e18
                return {"eth_balance": round(eth, 6), "address": WALLET}
        return {"error": "Could not fetch balance"}
    except Exception as e:
        return {"error": str(e)}

def check_recent_transactions():
    """Check last 5 transactions on wallet."""
    try:
        r = requests.get(
            ETHERSCAN_API,
            params={
                "module": "account",
                "action": "txlist",
                "address": WALLET,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": 5,
                "sort": "desc"
            },
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "1":
                txs = []
                for tx in data.get("result", []):
                    txs.append({
                        "hash": tx["hash"][:16] + "...",
                        "from": tx["from"][:10] + "...",
                        "to": tx["to"][:10] + "..." if tx.get("to") else "Contract",
                        "value_eth": round(int(tx["value"]) / 1e18, 6),
                        "date": datetime.fromtimestamp(int(tx["timeStamp"])).strftime("%Y-%m-%d %H:%M")
                    })
                return txs
        return []
    except:
        return []

def read_pending_tasks():
    """Read pending tasks from Recent_State or bootstrap."""
    pending_file = os.path.join(NAS_PATH, "00_SISTEMA", "BOOTSTRAP_OPTIMIZADO_DANA_v1.2.md")
    try:
        with open(pending_file, "r", encoding="utf-8") as f:
            content = f.read()
            # Extract pending section if exists
            if "Pendiente" in content or "TODO" in content:
                return "Ver bootstrap para tareas pendientes"
    except:
        pass
    return "No se pudo leer tareas pendientes"

def generate_briefing():
    """Generate the daily briefing markdown file."""
    timestamp = get_timestamp()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Gather data
    moltbook_data = check_moltbook()
    wallet_data = check_wallet()
    transactions = check_recent_transactions()
    pending = read_pending_tasks()
    
    # Build briefing
    lines = []
    lines.append(f"# BRIEFING DIARIO — {date_str}")
    lines.append(f"**Generado:** {timestamp}")
    lines.append(f"**Sistema:** Briefing automático v1.0")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Moltbook section
    lines.append("## MOLTBOOK")
    lines.append("")
    for i, post in enumerate(moltbook_data):
        if "error" in post:
            lines.append(f"**Post {i+1}:** Error — {post['error']}")
        else:
            lines.append(f"### {post['title']}")
            lines.append(f"- Upvotes: {post['upvotes']} | Downvotes: {post['downvotes']} | Comentarios: {post['comment_count']}")
            if post['comments']:
                lines.append(f"- **Últimos comentarios:**")
                for c in post['comments'][-3:]:  # last 3 comments
                    lines.append(f"  - **{c['author']}** ({c['created_at'][:10]}): {c['content'][:150]}...")
            lines.append("")
    
    # Wallet section
    lines.append("## WALLET")
    lines.append("")
    if "error" in wallet_data:
        lines.append(f"Error: {wallet_data['error']}")
    else:
        lines.append(f"- **Dirección:** {wallet_data['address']}")
        lines.append(f"- **Balance ETH:** {wallet_data['eth_balance']}")
    lines.append("")
    
    if transactions:
        lines.append("### Últimas transacciones")
        for tx in transactions:
            lines.append(f"- {tx['date']} | {tx['value_eth']} ETH | {tx['hash']}")
        lines.append("")
    
    # Status section
    lines.append("## ESTADO GENERAL")
    lines.append("")
    lines.append(f"- **Agent ID:** #23980 (ERC-8004)")
    lines.append(f"- **Moltbook:** Suspendida hasta ~18 feb 2026 (offense #2)")
    lines.append(f"- **IAK:** 6/7 módulos completados")
    lines.append(f"- **Pendiente:** {pending}")
    lines.append("")
    lines.append("---")
    lines.append(f"*Generado automáticamente. Próximo briefing: mañana.*")
    
    # Write file
    briefing_content = "\n".join(lines)
    
    # Write to daily file
    daily_file = os.path.join(BRIEFING_DIR, f"BRIEFING_{date_str}.md")
    with open(daily_file, "w", encoding="utf-8") as f:
        f.write(briefing_content)
    
    # Also write to "latest" file (always overwritten)
    latest_file = os.path.join(BRIEFING_DIR, "BRIEFING_ULTIMO.md")
    with open(latest_file, "w", encoding="utf-8") as f:
        f.write(briefing_content)
    
    print(f"Briefing generado: {daily_file}")
    print(f"Briefing último: {latest_file}")
    return briefing_content

if __name__ == "__main__":
    content = generate_briefing()
    print("\n" + "="*50)
    print(content)
