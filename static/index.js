const table_body = document.querySelector('tbody');
let last_fetch_result;

async function getCurrentGames() {
    const url = window.location.protocol + "//" + window.location.host + "/api/games/";
    // Default options are marked with *
    const response = await fetch(url, {
      cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
      credentials: 'same-origin', // include, *same-origin, omit
      headers: {
        'Content-Type': 'application/json'
      },
      referrerPolicy: 'no-referrer',
    });
    const games = await response.json();
    if (games != last_fetch_result) {
        const trs = document.querySelectorAll('tbody tr');
        trs.forEach(tr => {
            tr.remove();
        })
        games.forEach(game => {
            const tr = document.createElement('tr');
            table_body.appendChild(tr);
            for (let index = 0; index < 7; index++) {
                switch (index) {
                    case 0:
                        let th1 = document.createElement('th');
                        th1.innerText = game.id;
                        tr.appendChild(th1);
                        break;
                    case 1:
                        let td2 = document.createElement('td');
                        td2.innerText = game.category;
                        tr.appendChild(td2);
                        break;
                    case 2:
                        let td3 = document.createElement('td');
                        td3.innerText = game.difficulty;
                        tr.appendChild(td3);
                        break;
                    case 3:
                        let td4 = document.createElement('td');
                        td4.innerText = game.amount;
                        tr.appendChild(td4);
                        break;
                    case 4:
                        let td5 = document.createElement('td');
                        td5.innerHTML = `<code>${game.players}</code>`;
                        tr.appendChild(td5);
                        break;
                    case 5:
                        let td6 = document.createElement('td');
                        td6.innerHTML = `<span class="tag is-success is-light">${game.status}</span>`;
                        tr.appendChild(td6);
                        break;
                    case 6:
                        console.log('are we here?')
                        if (game.status != "in_progress" || game.status != "finished") {
                            let td7 = document.createElement('td');
                            td7.innerHTML = `<a href="/game/${game.id}/" class="button is-link">Join</a>`;
                            tr.appendChild(td7);
                        }
                        break;
                }
            }
        })
    }
    last_fetch_result = games;
  }

document.addEventListener('DOMContentLoaded', () => {
    getCurrentGames().catch(error => {
        console.log(error);
    });
    setInterval(() => {
        getCurrentGames().catch(error => {
            console.log(error);
        });
    }, 10000);
});