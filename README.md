# 🧠 Minion

> Decode. Analyze. Learn. Attack.

🔓 **Kickstart your cybersecurity journey with Minion.**  
Minion is a beginner-friendly, CTF-ready security toolkit that helps you decode payloads, analyze logs, crack hashes, and run recon — all in one clean, accessible interface.

---

## ✨ Why Minion?

- 💡 For beginners AND operators — no steep learning curve
- 📦 All-in-one — decoding, pipeline building, scanning, note-keeping
- 🧠 Prioritizes readable output — not just decoding, but understanding
- 🕵️ Triage artifacts fast — discover obfuscated strings, tokens, hashes

---

## 🔐 Features

### Forensics & Decoding

- Decode layers of Base64, Hex, Binary, Base85, URL, and classical ciphers: Caesar (±1–13), ROT13, Atbash
- Recursive decoding chains with scoring and confidence ranking
- Real word detection using Kali-native wordlists
- Metadata Extraction with exiftool
- Embedded File Analysis using binwalk
- File Signature Identification via the file utility
- Deduplication, transform trail tracking, and readability scoring
- Recursive decoding paths with auto-prioritized scoring
- Real word detection via built-in Kali wordlist
- Smart filters: deduplication, path chaining, confidence tagging

### Offensive Security

- Run Nmap, Gobuster, SMB tools from GUI
- Wordlist generation and mutation
- Hash ID + cracking with John, Hashcat, Hydra, CME
- Payload readability scoring (for red team validation)

### Log Analysis Engine

- Grep | Cut | AWK | Sort | Uniq builder
- Smart delimiter selection, including custom delimiters
- Inline syntax tips and usage examples
- Real-time output streaming into the GUI during execution





### Learner Tools

- JSON-based cheat sheets (user-editable)
- Auto-launched terminal
- Command history tracking
- In-app note system

---

## 📥 Getting Started

```bash
[git clone https://github.com/ttehsec/Minion3.0.git]
cd Minion3.0
python3 minionGUI.py
