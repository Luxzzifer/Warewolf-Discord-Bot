# 🐺 Werewolf Discord Bot

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3.2-green.svg)](https://github.com/Rapptz/discord.py)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/Luxzzifer/Warewolf-Discord-Bot/releases)

---
![Warewolf Bot GUI](/Pic/Readmd/image.png))
## 🇮🇩 Indonesia

### 📖 Deskripsi
Werewolf Discord Bot adalah bot Discord  yang berjalan dengan local memungkinkan Anda bermain game Werewolf secara otomatis di server Discord Anda. Bot ini dilengkapi dengan GUI (Graphical User Interface) yang memudahkan pengaturan dan menjalankan bot.

### ✨ Fitur Utama
- 🎮 **Game Werewolf Lengkap** - Mendukung hingga 10 pemain dengan berbagai role
- 🎭 **Role Beragam** - Werewolf, Seer, Tough Guy, Witch, Laycan, Villager
- 🌙 **Fase Malam** - Werewolf membunuh, Seer menerawang, Witch menyelamatkan
- 🗳️ **Sistem Voting** - Voting untuk mengeksekusi pemain yang dicurigai
- 🖥️ **GUI Modern** - Antarmuka grafis yang mudah digunakan
- 🔌 **Auto Reconnect** - Bot akan mencoba terhubung kembali jika terputus
- 📊 **Status Monitoring** - Monitor status bot dan koneksi internet

### 🎮 Role dan Kemampuan

| Role | Alignment | Kemampuan |
|------|-----------|-----------|
| 🐺 Werewolf | Jahat | Membunuh satu pemain setiap malam (hanya 1 per malam) |
| 🔮 Seer | Baik | Melihat alignment (Baik/Jahat) seorang pemain |
| 🛡️ Tough Guy | Baik | Membutuhkan 2 kali serangan untuk mati |
| 🧙 Witch | Baik | Memiliki ramuan penyelamat (1x) |
| 🌾 Laycan | Jahat | Warga desa biasa jika diterawang seer, aligmentnya jahat |
| 🏘️ Villager | Baik | Warga biasa tanpa kemampuan khusus |

### 📝 Command

| Command | Deskripsi |
|------|-----------|
| /setmod | Pilih moderator game |
| /start | Memuali Game (Hanya moderator) | 
| /night | Mulai Fase malam (moderator)|
| /kill | Warewolf membunuh pemain | 
|/vote | Memulai sesi voting (moderator) | 
| /end | Mengakhiri game (moderator) | 

### 📋 Persyaratan Sistem

- **Python** 3.8 atau lebih baru
- **Discord Bot Token** (dapatkan dari [Discord Developer Portal](https://discord.com/developers/applications))
- **Koneksi internet** yang stabil
- **Library Python** (akan diinstall otomatis)

### 🔑 Cara Mendapatkan Token Bot Discord

#### 1: Buka Discord Developer Portal
```bash
https://discord.com/developers/applications
```

#### 2: Buat Aplikasi Baru
1. Klik tombol **"New Application"** di pojok kanan atas

2. Masukkan nama aplikasi (contoh: **Werewolf Bot**)

4. Centang kotak persetujuan dan klik "**Create**"

#### 3: Buat Bot
1. Di menu sebelah kiri, klik "**Bot**"

2. Klik tombol "**Add Bot**"

3. Konfirmasi dengan klik "**Yes, do it!**"
#### 4: Dapatkan Token Bot
1. Di bagian "**Token**", klik "**Reset Token**"

2. Konfirmasi dengan klik "**Yes, do it!**"

3. Copy token yang muncul
```bash
Contoh token: MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.Gxxxxx.xxxxx-xxxxx_xxxxx
```
⚠️ PENTING: Token ini bersifat rahasia! Jangan bagikan ke siapapun!

#### 5: Invite Bot ke Server
1. Di menu sebelah kiri, klik "**OAuth2**" → "**URL Generator**"

2. Di bagian "**Scopes**", centang:

    - ✅ bot
    - ✅ applications.commands
3. Di bagian "**Bot Permissions**", pilih permission yang diperlukan:

    - ✅ Send Messages
    - ✅ Manage Messages
    - ✅ Embed Links
    - ✅ Read Message History
    - ✅ Use Slash Commands

Copy URL yang dihasilkan, paste di browser baru, pilih server, dan klik "**Authorize**"

## 📚 Referensi

- [Discord Developer Portal](https://discord.com/developers/applications)
- [Discord API Documentation](https://discord.com/developers/docs/intro)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)

## ⚠️ Pemecahan Masalah

### ❌ Bot Tidak Online
- Periksa kembali token yang Anda masukkan
- Pastikan token sudah di-reset dan disalin dengan benar
- Cek apakah koneksi internet Anda berfungsi

### ❌ Command Tidak Muncul
- Tunggu 1-2 menit, terkadang perlu waktu untuk sinkronisasi
- Periksa apakah bot memiliki izin `Use Slash Commands`
- Restart bot dengan klik STOP lalu START

### ❌ Bot Tidak Bisa Mengirim DM
- Pastikan pengguna mengizinkan DM dari member server
- Atau atur di server: Pengaturan Server → Privasi → "Izinkan pesan langsung dari member server"

### ❌ Error "Improper token"
- Token tidak valid, reset token di Developer Portal dan salin kembali

---

### 🔒 Tips Keamanan

1. **Jangan pernah membagikan token bot** kepada siapapun
2. **Simpan token di file `.env`** (gunakan python-dotenv)
3. **Jangan commit token ke GitHub**
4. **Reset token** jika Anda curiga telah bocor

---
---
### 🚀 Cara Instalasi

#### 1. Clone Repository
```bash
git clone https://github.com/yourusername/werewolf-discord-bot.git
cd werewolf-discord-bot
pip install -r requirements.txt
```

## 🇬🇧 English

### 📖 Description
Werewolf Discord Bot is a locally-run Discord bot that allows you to play the Werewolf game automatically on your Discord server. The bot comes with a GUI (Graphical User Interface) for easy configuration and management.

### ✨ Features
- 🎮 **Full Werewolf Game** – Supports up to 10 players with various roles
- 🎭 **Diverse Roles** – Werewolf, Seer, Tough Guy, Witch, Laycan, Villager
- 🌙 **Night Phase** – Werewolf kills, Seer sees, Witch saves
- 🗳️ **Voting System** – Vote to execute suspected players
- 🖥️ **Modern GUI** – Easy-to-use graphical interface
- 🔌 **Auto Reconnect** – Bot attempts to reconnect if disconnected
- 📊 **Status Monitoring** – Monitor bot status and internet connection

### 🎮 Roles and Abilities

| Role | Alignment | Ability |
|------|-----------|---------|
| 🐺 Werewolf | Evil | Kills one player each night (only 1 per night) |
| 🔮 Seer | Good | Sees alignment (Good/Evil) of a player |
| 🛡️ Tough Guy | Good | Requires 2 attacks to die |
| 🧙 Witch | Good | Has a save potion (1x) |
| 🌾 Laycan | Evil | Ordinary villager but appears Evil to Seer |
| 🏘️ Villager | Good | Ordinary villager with no special abilities |

### 📝 Commands

| Command | Description |
|---------|-------------|
| `/setmod` | Select game moderator |
| `/start` | Start the game (moderator only) |
| `/night` | Start night phase (moderator only) |
| `/endnight` | End night phase (moderator only) |
| `/kill` | Werewolf kills a player |
| `/terawang` | Seer sees a player |
| `/vote` | Start voting session (moderator only) |
| `/end` | End the game (moderator only) |
| `/status` | Check game status (moderator only) |
| `/guide` | Game guide |

### 📋 System Requirements
- Python 3.8 or newer
- Discord Bot Token (get from [Discord Developer Portal](https://discord.com/developers/applications))
- Stable internet connection

## 🔑 How to Get a Discord Bot Token

### Step 1: Open Discord Developer Portal
Open your browser and go to:
Log in with your Discord account.

### Step 2: Create a New Application
1. Click the **"New Application"** button in the top right corner
2. Enter an application name (example: `Werewolf Bot`)
3. Check the agreement box and click **"Create"**

### Step 3: Create a Bot
1. In the left sidebar, click **"Bot"**
2. Click the **"Add Bot"** button
3. Confirm by clicking **"Yes, do it!"**

### Step 4: Get the Bot Token
1. In the **"Token"** section, click **"Reset Token"**
2. Confirm by clicking **"Yes, do it!"**
3. **Copy** the token that appears
```bash
Example token: MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.Gxxxxx.xxxxx-xxxxx_xxxxx
```

⚠️ **IMPORTANT:** This token is secret! Do not share it with anyone!

### Step 5: Enable Privileged Gateway Intents
Scroll down to the **"Privileged Gateway Intents"** section and enable:
- ✅ **MESSAGE CONTENT INTENT** (Required to read messages)
- ✅ **SERVER MEMBERS INTENT** (Required for member data)

Click **"Save Changes"** after enabling.

### Step 6: Invite Bot to Your Server
1. In the left sidebar, click **"OAuth2"** → **"URL Generator"**
2. In the **"Scopes"** section, check:
- ✅ `bot`
- ✅ `applications.commands`
3. In the **"Bot Permissions"** section, select the required permissions:
- ✅ `Send Messages`
- ✅ `Manage Messages`
- ✅ `Embed Links`
- ✅ `Read Message History`
- ✅ `Use Slash Commands`
4. **Copy** the generated URL, paste it in a new browser tab, select your server, and click **"Authorize"**

---


## ⚠️ Troubleshooting

### ❌ Bot Not Online
- Double-check the token you entered
- Make sure the token was reset and copied correctly
- Check if your internet connection is working

### ❌ Commands Not Showing
- Wait 1-2 minutes, sometimes it takes time to sync
- Check if the bot has the `Use Slash Commands` permission
- Restart the bot by clicking STOP then START

### ❌ Bot Can't Send DMs
- Make sure users allow DMs from server members
- Or configure in server: Server Settings → Privacy → "Allow direct messages from server members"

### ❌ "Improper token" Error
- Token is invalid, reset the token in Developer Portal and copy again

---


## 📚 References

- [Discord Developer Portal](https://discord.com/developers/applications)
- [Discord API Documentation](https://discord.com/developers/docs/intro)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)

---

By following this tutorial, you will have a bot token ready to use with the Werewolf Discord Bot! 🎮🐺

### 🚀 Installation

#### 1. Clone Repository
```bash
git clone https://github.com/yourusername/werewolf-discord-bot.git
cd werewolf-discord-bot
pip install -r requirements.txt

