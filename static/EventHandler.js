export default class EventHandler {
    constructor(game) {
        this.game = game;
    }
    finishGame(event) {
        // if the game is finished
        this.game.progressBar.remove();
        this.game.gameTitle.innerText = "The game is over!";
        event.players.forEach(player => {
            const el = document.createElement('tr');
            const username_col = document.createElement('th');
            username_col.innerText = player.username;
            const points_col = document.createElement('th');
            points_col.innerText = player.points;
            el.appendChild(username_col);
            el.appendChild(points_col);
            this.game.table_body.appendChild(el);
        })
        let n = 30;
        this.game.getChoices().forEach(choice => {
            choice.remove();
        });
        setInterval(() => {
            if (n != 1) {
                n--;
                this.game.gameTitle.innerText = `The game is over! Redirecting in ${n} seconds`;
            } else {
                window.location.replace(window.location.protocol + "//" + window.location.host);
            }
        }, 1000);
    }
    showQuestion(event) {
        this.game.choices_div.innerHTML = '';
        message.classList.add('is-hidden');
        let num = 0;
        setInterval(() => {
            if (num != 30) {
                num++;
                this.game.progressBar.value = num.toString();
                this.game.progressBar.innerText = num.toString() + "%";
            }
        }, 1000);
        title.innerHTML = event.question.question;
        this.game.current_question_text.innerText = `Question ${event.question.current_question_id} of ${event.question.total_questions}`;
        event.question.choices.forEach(choice => {
            const button = document.createElement('button');
            button.className = 'button choice is-info is-fullwidth is-round is-large mb-3';
            button.innerHTML = choice;
            button.addEventListener('click', () => {
            this.game.socket.send(JSON.stringify({"type": "answer", "choice": button.innerHTML}));
            this.game.getChoices().forEach(choice => {
                    choice.disabled = true;
                });
            });
            this.game.choices_div.appendChild(button);
        });
    }
    showResult(event) {
        this.game.message.classList.remove('is-hidden');
        const message = this.game.message;
        if (event.result == "correct") {
            message.innerHTML = "That answer is correct!";
            message.classList.remove('is-danger');
            message.classList.add('is-success');
        } else {
            message.innerHTML = `That answer is incorrect. The correct answer was: ${event.correct_answer}.`;
            message.classList.add('is-danger');
            message.classList.remove('is-success');
        }
    }
    startGame(e) {
        this.game.socket.send(JSON.stringify({"type": "start"}));
    }

}
