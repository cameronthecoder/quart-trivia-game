import EventHandler from './EventHandler.js';

const fireSnackbar = (message, seconds = 3) => {
    var snackbar = document.getElementById("snackbar");
    snackbar.innerHTML = message;
    snackbar.className = 'show';
    playNotification();
    setTimeout(function(){ snackbar.className = snackbar.className.replace("show", ""); }, 1000 * seconds);
};

const playNotification = () => {
    var audio = new Audio('/static/notification.mp3');
    audio.play();
}

let Game = {
    id: null,
    category: null,
    players: 1,
    player: {
        username: null,
        host: false
    },
    status: null,
    init () {
        this.socket = new WebSocket(`wss://${window.location.host}${window.location.pathname}`);
        this.socket.addEventListener('open', e => this.onSocketOpen(e));  
        this.eventHandler = new EventHandler(this);
        this.socket.addEventListener('message', e => this.onSocketMessage(e));
        this.socket.addEventListener('close', e => this.onSocketClose(e));
        this.startButton = document.getElementById('start');
        this.startButton.addEventListener('click', e => this.eventHandler.startGame(e));
        this.gameTitle = document.getElementById('title');
        this.progressBar = document.getElementById('progress');
        this.gameInfo = document.getElementById('info');
        this.player_count = document.getElementById('players');
        this.choices_div = document.getElementById('choices');
        this.message = document.getElementById('message');
        this.current_question_text = document.getElementById('current_question_text');
        this.table_body = document.querySelector('table tbody');
    },
    onSocketOpen(e) {
        console.info('Connected to WebSocket Server!');
        let username = prompt('Please enter a username: ');
        while (username == "") {
            username = prompt('Please enter a username: ');
            if (username != "") {
                break;
            }
        }
        if (username == null) {
            window.location.replace(window.location.protocol + "//" + window.location.host);
        }
        this.player.username = username;
        fireSnackbar('Connected!');
        this.socket.send(JSON.stringify({"type": "connect", "username": username}));
    },
    onSocketMessage(e) {
        const data = JSON.parse(e.data);
        if (data.event) {
            this.handleEvent(data.event);
        }
    },
    handleEvent(event) {
        switch (event.type) {
            case "info":
                if (event.status == "waiting") {
                    this.gameTitle.innerText = `Welcome ${this.player.username}! Waiting for players...`;
                    this.player_count.innerText = event.clients_connected;
                    this.startButton.disabled = (event.clients_connected > 1) ? false : true;
                } else if (event.status == "finished") {
                    this.eventHandler.finishGame(event);
                }
                break;
            case "start":
                this.gameTitle.innerText = "Game starting..."
                fireSnackbar('The game is starting. Good luck!');
                this.gameInfo.remove();
                document.title = "Trivia Game - In progress"
                this.startButton.remove();
                break;
            case "question":
                this.eventHandler.showQuestion(event);
                break;
            case "choice_response":
                playNotification();
                this.eventHandler.showResult(event);
                break;
            case "player_connected":
                fireSnackbar(`${event.username} connected`)
                break;
            case "player_left":
                fireSnackbar(`${event.username} left`)
                break;
            case "new_host":
                setTimeout(function() { fireSnackbar("The host has left. You are the new host of the game."); }, 5000);
                break;
        }
    },
    onSocketClose() {
        alert("The WebSocket connection was closed.");
        window.location.replace(window.location.protocol + "//" + window.location.host);
    },
    onSocketError(e) {
        fireSnackbar("WebSocket Error, please check the console.");
        console.log(e);
    },
    getChoices() {
        return document.querySelectorAll('.choice');
    }
};

window.onload = () => {
    Game.init();
}
