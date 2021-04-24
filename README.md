# CacheCohSimWeb
### Interactive Web-based Simulator for Various Cache Coherence Protocols

This simulator is designed for the final project of Win2021 University of Michigan EECS570 course. It is an interactive web-based simulator that supports snoop-based MSI, snoop-based MESI and directory-based MSI cache coherence protocols.

## 1. Prerequisites
### 1.1. **Operating System**
Please make sure you use Ubuntu 18.04 LTS for setting up the server.

### 1.2. **Node JS**
Clone the repository. In the repo directory:
```
    cd ./www
    sudo apt-get install nodejs npm
    npm install .
```

## 2. Start the Server
In the repo directory:
```
    cd ./www
    npm start
```

## 3. Run the Web Front-end
On the same computer as the server, open a browser window and visit http://localhost:3000. Now you can play with the simulator!

