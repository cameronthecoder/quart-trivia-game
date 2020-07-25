const socket = new WebSocket(`ws://${window.location.host}${window.location.pathname}`);
const start = document.getElementById('start');
const title = document.getElementById('title');
const progressBar = document.getElementById('progress');
const info = document.getElementById('info');
const choice_div = document.getElementById('choices');
const message = document.getElementById('message');
const current_question_text = document.getElementById('current_question_text');

socket.onopen = () => {
    console.log('Connected to WebSocket Server!');
    const username = prompt('Please enter a username: ');
    socket.send(JSON.stringify({"type": "connect", "username": username}));
};


const shuffle = (array) => {
    var currentIndex = array.length, temporaryValue, randomIndex;
  
    // While there remain elements to shuffle...
    while (0 !== currentIndex) {
  
      // Pick a remaining element...
      randomIndex = Math.floor(Math.random() * currentIndex);
      currentIndex -= 1;
  
      // And swap it with the current element.
      temporaryValue = array[currentIndex];
      array[currentIndex] = array[randomIndex];
      array[randomIndex] = temporaryValue;
    }
  
    return array;
  }

socket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    switch (data.event.type) {
        case "info":
            if (data.event.status == "waiting") {
                document.getElementById('players').innerText = data.event.clientsConnected;
                start.disabled = (data.event.clientsConnected > 1) ? false : true;
            } else if (data.event.status == "finished") {
                title.innerText = "The game is over!";
                const scores = data.event.players.toString();
                const fdsdsf = document.createElement('code')
                fdsdsf.innerHTML = scores;
                title.appendChild(fdsdsf);
                let n = 10;
                document.querySelectorAll('.choice').forEach(choice => {
                    choice.remove();
                });
                setInterval(() => {
                    if (n != 1) {
                        n--;
                        title.innerText = `The game is over! Redirecting in ${n} seconds`;
                    } else {
                        window.location.replace(window.location.protocol + "//" + window.location.host);
                    }
                }, 1000);
            }
            break;
        case "start":
            title.innerText = "Game starting..."
            info.remove();
            start.remove();
            break;
        case "question":
            choice_div.innerHTML = '';
            message.classList.add('is-hidden');
            let num = 0;
            setInterval(() => {
                if (num != 30) {
                    num++;
                    progressBar.value = num.toString();
                    progressBar.innerText = num.toString() + "%";
                }
            }, 1000);
            title.innerHTML = data.event.question.question;
            current_question_text.innerText = `Question ${data.event.question.current_question_id} of ${data.event.question.total_questions}`
            data.event.question.choices.forEach(choice => {
                const button = document.createElement('button');
                button.className = 'button choice is-info is-fullwidth is-round is-large mb-3';
                button.innerHTML = choice;
                button.addEventListener('click', () => {
                    socket.send(JSON.stringify({"type": "answer", "choice": button.innerHTML}));
                    document.querySelectorAll('.choice').forEach(choice => {
                        choice.disabled = true;
                    });
                });
                choice_div.appendChild(button);
            });
            break;
        case "choice_response":
            message.classList.remove('is-hidden');
            if (data.event.result == "correct") {
                message.innerHTML = "That answer is correct!";
                message.classList.remove('is-danger');
                message.classList.add('is-success');
            } else {
                message.innerHTML = `That answer is incorrect. The correct answer was: ${data.event.correct_answer}.`;
                message.classList.add('is-danger');
                message.classList.remove('is-success');
            }
            break;
        }
    }

start.onclick = () => {
    socket.send(JSON.stringify({"type": "start"}));
}

socket.onerror = (e) => {
    console.log(e);
};

socket.onclose = (e) => {
    alert('Connection was closed!')
}