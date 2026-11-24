# Tool-X GUI

Ek web-based dashboard jo `core/data.json` aur `core/cat.json` ko padh ke
saare 371 tools ko icon-wale cards me dikhata hai. Click karke install karo —
koi sudo / password prompt nahi aayega.

## Chalane ka tarika

### Linux / Termux

```bash
cd Tool-X/gui
chmod +x run.sh
./run.sh
```

Agar `run.sh` chalane me dikkat aaye, manually bhi chala sakte ho:

```bash
pip3 install --user flask
python3 app.py
```

### Windows

`gui` folder ke andar **`run.bat`** pe double-click karo.

Ya Command Prompt / PowerShell se:

```cmd
cd Tool-X\gui
pip install flask
python app.py
```

Dono case me phir apne browser me kholo: **http://127.0.0.1:5000**

**Windows pe ek zaroori baat:** Python installed hona chahiye aur "Add Python to
PATH" option tick hona chahiye install ke waqt (https://python.org se
download karte waqt). Agar `python` command not found aaye, Python dubara
install karo aur wo checkbox zaroor tick karo. Git bhi installed hona
chahiye (https://git-scm.com) taaki tools clone ho sakein.

**Limitation:** `apt`/`pkg`-type tools (nmap, hydra, jaise system package se
aane wale) Windows pe kaam nahi karenge kyunki Windows me apt/yum/pkg hota
hi nahi — GUI tumhe clearly bata dega "No supported package manager found".
GitHub-based tools (`git clone` wale, jo zyadatar hain) Windows pe clone to
ho jayenge, par kai khud security/hacking tools **sirf Linux kernel
features** (jaise wifi monitor mode, raw sockets) use karte hain — wo clone
hone ke baad bhi Windows pe chalenge nahi. Behtar results ke liye Linux ya
WSL (Windows Subsystem for Linux) use karna recommended hai.

## Ye kaise kaam karta hai

- **Sidebar** — saari 15 categories, har ek apna icon ke saath. Click karke
  sirf us category ke tools dikhte hain.
- **Search bar** — top pe, kisi bhi tool ka naam type karke turant filter ho
  jata hai.
- **Tool card** — har tool ka apna icon (category ke hisaab se), naam,
  package manager (git/apt/curl), aur category tags.
- **Install button** — click karte hi background me install start hota hai.
  Button khud "Installing..." dikhata hai, phir "Installed" ya "Retry install"
  (agar fail ho gaya) me badal jata hai.
- **Log panel** (neeche-right corner) — har tool ka live install log yahan
  dikhta hai — exact wahi output jo terminal me dikhta.

## Install kahan hota hai

Saare `git`/`curl` wale tools **`gui/installed/`** folder ke andar clone hote
hain — system ki koi file nahi chhoti, isliye **kabhi root/sudo nahi chahiye**.

`apt`/`pkg`-wale tools (jaise nmap, python) system package manager se aate
hain — agar tum root nahi ho, card pe "Needs sudo" dikhega aur log me exact
command milegi jo tumhe manually chalani hogi (jaise `sudo apt-get install
nmap -y`), kyunki password prompt kabhi nahi dikhaya jaata.

## Zaroori cheezein

- Python 3
- Flask (`run.sh` khud install kar dega, `pip3 install --user flask`)
- Internet connection (GitHub se clone karne ke liye)
