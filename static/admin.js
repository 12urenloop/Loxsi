const COLORS = [
    'blue',
    'green',
    'cyan',
    'red',
    'purple',
    'yellow',
    'orange'
];

// region Websocket
let websocket = new WebSocket(`ws://${location.host}/feed`);

websocket.onopen = (_event) => {
    document.getElementById('chart-message').remove();
};

websocket.onmessage = (event) => {
    let data = JSON.parse(event.data)
    if (!('ping' in data)) {
        console.log(data)
        if (data['topic'] === 'counts') {
            setData(data.data);
        } else if (data['topic'] === 'message') {
            setMessage(data.data);
        } else if (data['topic'] === 'frozen') {
            setFrozen(data.data)
        }
    }
};

websocket.onclose = (_event) => {
}

// region Admin feed
let admin_feed = new WebSocket(`ws://${location.host}/admin/feed`);

admin_feed.onopen = () => {
    document.getElementById('active-source').innerText = "Connecting..."
    document.getElementById('active-connections').innerText = "Connecting..."
    document.getElementById('sources').innerHTML =
        '<div class="col l6 m12 s12" style="margin-top: 20px">Connecting...</div>'
}

let message_handlers = {
    'telraam-health': data => {
        let root = document.getElementById('root')
        if (data === 'bad') {
            root.classList.remove('tui-bg-blue-black')
            root.classList.add('tui-bg-red-black')
        } else {
            root.classList.remove('tui-bg-red-black')
            root.classList.add('tui-bg-blue-black')
        }
    },
    'active-source': data => {
        document.getElementById('active-source').innerText = data['name']
    },
    'lap-source': data => {
        let sources = document.getElementById('sources')
        sources.innerHTML = ""
        for (let lap_source of data) {
            console.log(lap_source)
            sources.innerHTML += '<div class="col l6 m12 s12" style="margin-top: 20px">' +
                `<button class="tui-button white-168 white-255-hover" onclick="use(this)" value="${lap_source.id}" style="width: 100%">` +
                `${lap_source.name} </button></div>`
        }
    },
    'active-connections': data => {
        document.getElementById('active-connections').innerText = `Count: ${data}`;
    },
    'freeze': data => {
        document.getElementById('freeze-time').value = new Date(data + (2 * 60 * 60 * 1000)).toISOString().substring(0, 16);
    }
}

admin_feed.onmessage = e => {
    let data = JSON.parse(e.data)
    if ('topic' in data && 'data' in data) {
        console.log(data)
        if (data['topic'] in message_handlers) {
            message_handlers[data['topic']](data['data'])
        }
    } else {
        if (!('ping' in data)) {
            console.error(`Invalid message in admin feed: ${data}`)
        }
    }
}
// endregion
// endregion

function use(element) {
    fetch(`/api/use/${element.value}`, {
        method: "POST"
    }).then(res => {
        console.log(res);
    })
}

async function sendMessage(message) {
    await fetch('/api/message', {
        method: "POST",
        body: JSON.stringify({
            message: message
        }),
        headers: {
            'Content-type': 'application/json; charset=UTF-8'
        }
    })
}

async function deleteMessage() {
    await fetch('/api/message', {
        method: "DELETE"
    })
}

async function sendTime(message) {
    await fetch('/api/freeze', {
        method: "POST",
        body: JSON.stringify({
            time: new Date(message).getTime()
        }),
        headers: {
            'Content-type': 'application/json; charset=UTF-8'
        }
    })
}

async function deleteTime() {
    await fetch('/api/freeze', {
        method: "DELETE"
    })
}

function setData(res) {
    if (!Array.isArray(res)) {
        console.error('Couldn\'t set teams bcs parsed WS data is not an array')
        return;
    }
    const chartElem = document.getElementById('chart');
    const chartLegendElem = document.getElementById('chart-legend');
    let highestCount = 0;
    for (let t of res) {
      if (t.count > highestCount) {
        highestCount = t.count;
      }
    };
    let colorIdx = 0;
    res.sort((a, b) => a.team.id - b.team.id).forEach(t => {
        // Search existing elem
        let chartValueEl = document.getElementById(t.team.id);
        if (!chartValueEl) {
            // create new
            chartValueEl = document.createElement('div');
            chartValueEl.id = t.team.id
            chartValueEl.classList.add('tui-chart-value', `${COLORS[colorIdx]}-168`);
            chartElem.append(chartValueEl)
            // Create legend name
            let chartLegendEl = document.createElement('div');
            chartLegendEl.classList.add("tui-chart-legend");
            chartLegendEl.innerText = t.team.name
            chartLegendElem.append(chartLegendEl)
        }
        chartValueEl.style.height = `${(t.count / (highestCount === 0 ? 1 : highestCount)) * 100}%`
        chartValueEl.innerText = t.count;
        colorIdx = (colorIdx + 1) % COLORS.length
    })
}

function setMessage(message) {
    document.getElementById('message').innerText = message;
}

function setFrozen(isFrozen) {
    document.getElementById('frozen-message').innerText = isFrozen ? 'Frozen: Yes' : 'Frozen: No'
}
