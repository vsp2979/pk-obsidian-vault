---

kanban-plugin: basic

---

## 📥 Backlog & Ideas

- [ ] **Voice Memos to Vault**: Auto-transcribe WhatsApp/Matrix voice notes with Gemini and file into Obsidian daily notes
- [ ] **Calendar Integration**: Connect Google Calendar / CalDAV to sync executive appointments and family schedules
- [ ] **Tesla Home Automation**: Automate Tesla Model 3 charging schedules via Home Assistant when solar/off-peak rates apply
- [ ] **DSPy + GEPA Self-Evolution**: Connect `hermes-agent-self-evolution` pipeline to systematically optimize skill prompts and tool descriptions
- [ ] **High Availability / Cloud Backup**: Automate offsite Proxmox VM backups to Oracle Cloud / Backblaze B2


## 📋 To Do / Priority Queue

- [ ] **Deploy Pi-Hole LXC (CT 101)**: Set up lightweight 512MB LXC container on Proxmox for local network ad-blocking and DNS #infra
- [ ] **Provision Home Assistant OS (HAOS VM 100)**: Run community installer for HAOS VM on Proxmox (3GB RAM, 2 vCPUs) #homeassistant
- [ ] **USB Zigbee Coordinator Passthrough**: Connect USB Zigbee/Z-Wave dongle to Proxmox host and pass through to HAOS VM #homeassistant
- [ ] **Hermes LXC Migration (CT 102)**: Run `/opt/hermes-matrix/scripts/proxmox/provision_hermes_lxc.sh` to migrate Hermes stack to homelab #infra
- [ ] **Generate HA Long-Lived Token**: Configure Home Assistant REST client in `.env` (`HOME_ASSISTANT_URL` and `HOME_ASSISTANT_TOKEN`) #homeassistant


## 🚀 In Progress

- [ ] **Thursday Parayan Reading Monitor**: Polling 6 groups at 9:00 AM, 12:00 PM, and 5:00 PM - 8:00 PM CST every Thursday #parayan
- [ ] **Daily Google Flights Watchdog**: Auditing DFW -> VGA/HYD/SFO/JFK fares daily at 8:00 AM CT via `flight_tracker.py` #travel
- [ ] **Automotive Financing Deal Scout**: Daily scan for sub-3% APR financing and dealer cash rebates at 8:00 AM CT #deals


## 🔍 Testing & Verification

- [ ] **Verify Parayan Message Regex**: Confirm number word normalization ("forty seven" -> 47) and combined chapters (16&17, 18&19, 43&44) #parayan
- [ ] **Receipt OCR & Deduplication**: Verify perceptual dhash and semantic duplicate detection in `FinanceAuditorAgent` #finance
- [ ] **LiteLLM Proxy Health Check**: Monitor DeepSeek-V3 / DeepSeek-R1 latency and readiness on port 4000 #ai


## ✅ Completed / Deployed

- [x] **Multi-User / Family Profiles**: Auto-detection by Matrix handle & WhatsApp JID, with shared family shopping vs private isolated todos and scoped memory
- [x] **Obsidian 5-Minute Vault Sync**: Hardened with conflict recovery abort-trap, log rotation (capped at 1K lines), and 5-min cron rebase
- [x] **Sub-Agent Modular Framework**: Built specialized agent hierarchy (`FamilyConciergeAgent`, `ParayanCoordinatorAgent`, `FinanceAuditorAgent`, `ResearchAgent`) in `agents/`
- [x] **Matrix Conduit Server**: Running lightweight Conduit Matrix homeserver on port 6167 with Element X integration
- [x] **WhatsApp Baileys Bridge**: Node.js bridge on port 5005 with privacy locks (drop DMs, whitelist family & parayan groups only)
- [x] **6 Parayan Groups Integrated**: Shama, Hemadpant, Tatya, Mahalsa, Dasganu, and Nanavali groups tracked
- [x] **Gemini Vision Roster Extraction**: Automated flyer table ingestion to JSON and SQLite `group_rosters`
- [x] **Special Reading Multi-Cycle Safeguard**: Support for festival readings (e.g. Punyatithi) with cycle archiving and clean Thursday re-arming
- [x] **SQLite WAL Storage Architecture**: Configured `secretary.db` with WAL mode and 5000ms busy timeout
- [x] **On-Demand Chat Commands**: Added `/parayan`, `/flights`, `/cardeals`, `/list`, `/remind`, `/note` across WhatsApp and Matrix


%% kanban:settings
```json
{"kanban-plugin":"basic","hide-card-count":false,"lane-width":280}
```
%%

