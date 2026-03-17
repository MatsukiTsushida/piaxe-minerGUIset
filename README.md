# THIS IS THE GUI VERSION OF THE PIAXE MINER BASED ON PyQt5 (WINDOWS SUPPORT)(16 chip set up with 2 integrated boards)


## Linux
1. Pull the repository
2. Open it in any code editor (I use Zed)
3. Run GUI.py

### Or run

```
sudo apt update
sudo apt upgrade

#if no python or git installed
sudo apt install python3
sudo apt install git

sudo apt install python3-pip

# clone repository
sudo git clone https://github.com/MatsukiTsushida/piaxe-minerGUIset.git
cd piaxe-minerGUIset

# and install requirements
sudo pip3 install -r requirements.txt --break-system-packages

# copy example files
cp config.yml.example config.yml
cp start_mainnet_publicpool_example.sh start.sh

cd piaxe-minerGUIset
#for 4 chips to collect (legacy version with 2 distinct hasboards)
sudo python3 GUInew.py




```

## Windows

1. Install WSL on your windows machine (https://learn.microsoft.com/en-us/windows/wsl/install-on-server)
2. Set it up and get any Debian based Distro
3. Install usbipd-win (https://github.com/dorssel/usbipd-win/releases/tag/v5.1.0)
4. Usbipd is needed to hook up your miners to wsl
5. Run terminal as administrator and type ``` usbipd list ```. This will list all of your usb devices
### <img width="946" height="238" alt="image" src="https://github.com/user-attachments/assets/c769f0fb-9ae0-4f3c-ad68-ac2eb425a4e0" />
6. In this case my microcontrollers are shared however if you are doing this the first time you need to share them first with ``` usbipd bind --busid <BUSID of usb> ```
7. Next step is to attach the usb device to WSL with ``` usbipd attach --wsl --busid <BUSID of usb> ```
8. After imputing ``` usbipd list ``` you should now see that they are attached:
### <img width="871" height="191" alt="image" src="https://github.com/user-attachments/assets/5c1bfd59-83f1-459a-a3a6-3f240b377062" />
9. Run terminal and start WSL by running ``` wsl.exe ```
10. Run
```
sudo apt update
sudo apt upgrade

#if no python or git installed
sudo apt install python3
sudo apt install git

sudo apt install python3-pip

# clone repository
sudo git clone https://github.com/MatsukiTsushida/piaxe-minerGUIset.git
cd piaxe-minerGUIset

# and install requirements
sudo pip3 install -r requirements.txt --break-system-packages

# copy example files
cp config.yml.example config.yml
cp start_mainnet_publicpool_example.sh start.sh

#installing all the graphics libraries WSL ONLY
sudo apt-get install libgl1-mesa-glx libegl1-mesa libxcb-randr0 libxcb-icccm4 libxcb-xfixes0 libxcb-shape0 libxcb-sync1 libxcb-xkb1 libxcb-render-util0 libsm6 libice6

cd piaxe-minerGUIset
#legacy or new version
sudo python3 GUInew.py

```
11. The repository should now be installed and the GUI and you can start the GUI with ``` python3 GUI.py ```




## SETTING UP POSTGRES WITH GRAFANA (both WSL and Linux)
1 Run this while being inside the project:
```
sudo apt-get install -y apt-transport-https software-properties-common wget

sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com beta main" | sudo tee -a /etc/apt/sources.list.d/grafana.list

# Updates the list of available packages
sudo apt-get update

# Installs the latest OSS release:
sudo apt-get install grafana

# Installs the latest Enterprise release:
sudo apt-get install grafana-enterprise

#start grafana
sudo systemctl daemon-reload
sudo systemctl start grafana-server

#setting up postgres
sudo apt-get update -y
sudo apt-get install -y postgresql postgresql-contrib
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '1324';"
sudo sed -i 's/local   all             all                                     peer/local   all             all                                     md5/g' "/etc/postgresql/$(ls /etc/postgresql | grep -E '^1[0-9]' | sort -V | tail -n 1)/main/pg_hba.conf"
sudo -u postgres psql -c "CREATE DATABASE postgres;"
sudo -u postgres psql postgres < "./backup.sql"
sudo systemctl restart postgresql

```
### 1.5 If the script is prompting to put the password in for the database, just put 1324 as the password each time(!IMPORTANT! MUST BE SPECIFICALLY 1324 UNLESS U CHANGE THE CODE IN GUIPY YOURSELF)

2. Run the GUI.py ``` python3 GUInew.py ``` and press ``` yes ```on the dialog window
3. Both grafana servers and postgres shoud be running now. Open http://localhost:3000/ for Grafana.
4. Input User: admin, password: admin. U will be propmted to change it, for the sake of easiness I would keep all the passwords as 1324
5. Go to Data Sources -> Add New Data Source Search for postgres (install if needed)
6. Set port: localhost:5432, Database name: postgres, user: postgres, password: 1324 -> Save and test. The test should be successful if not, go into terminal or WSL and run ``` sudo systemctl start postgresql ```
7.Go to Dashboards -> New -> Import, put the text from the json file in the project directory into the json imput underneath of just drag and drop the json.
8. After saving the dashboard open it, click 3 dots on the visulization and click edit
9. On the sources drop down click the source you just added and press save visulization
10. Now when running the miner with GUI.py the graph will update



# ↓ README FROM THE MAIN BRANCH ↓


# Hardware

PiAxe-Miner is the software needed to run the PiAxe and QAxe.

The repository with design files, BOM, ... can be found [here](https://github.com/shufps/piaxe)!


# Stratum Client Software

Fork of: https://github.com/crypto-jeronimo/pyminer <br>
Changes: 

- Removed Scrypt hashing and added Miner class
- Made it work with Python3
- added [PiAxe](https://github.com/shufps/piaxe) and [QAxe](https://github.com/shufps/qaxe) as miner
- added reconnect logic on broken connections

Influx and Grafana
==================

The repository contains a dockered setup running on the Pi that shows some statistics:



<img src="https://github.com/shufps/piaxe-miner/assets/3079832/8d34ec13-15bd-4dd4-abd3-9588c823c494" width="600px"/>

The "blocks found" counter is static of course ... 

PyMiner
=======

Currently supported algorithms:
- `sha256d`: SHA256d


Usage
-----
```
    python pyminer.py [-h] [-o URL] [-u USERNAME] [-p PASSWORD]
                         [-O USERNAME:PASSWORD] [-a ALGO] [-B] [-q]
                         [-P] [-d] [-v]

    -o URL, --url=              stratum mining server url
    -u USERNAME, --user=        username for mining server
    -p PASSWORD, --pass=        password for mining server
    -O USER:PASS, --userpass=   username:password pair for mining server

    -B, --background            run in the background as a daemon

    -q, --quiet                 suppress non-errors
    -P, --dump-protocol         show all JSON-RPC chatter
    -d, --debug                 show extra debug information

    -h, --help                  show the help message and exit
    -v, --version               show program's version number and exit


    Example:
        python pyminer.py -o stratum+tcp://foobar.com:3333 -u user -p passwd
```

---

# Setup Instructions

## Requirements
- Raspberry Pi 3 (Pi Zero doesn't run influx)
- Python 3.x PIP

## Installation

```
# install pip3
sudo apt install python3-pip

# clone repository
git clone https://github.com/shufps/piaxe-miner
cd piaxe-miner

# and install requirements
pip3 install -r requirements.txt --break-system-packages

# copy example files
cp config.yml.example config.yml
cp start_mainnet_publicpool_example.sh start.sh
```
In the new `start.sh` insert your `bc1...` address.

After copying the example files, edit them. The `config.yml` probably doesn't need changes if connecting a QAxe+.

### PiAxe
Depending on your Device change between
`piaxe` and `qaxe` in the `miner` setting.

Make sure to change to the correct USB Serial `PiAxe`:
```
  serial_port: "/dev/ttyS0"
``` 

### If running on Pi Zero (1 or 2)
Disable the influx or point it to your externally managed influxdb, with the most recent changes the pi zero can no longer run grafana.


## Start the miner

Change `start_mainnet_publicpool_example.sh` to your needs.


