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
  setData(event.data)
};

websocket.onclose = (_event) => {
  document.getElementById('chart-timer').parentElement.innerText = "Connection Lost ...";
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
    document.getElementById('active-connections').innerText = `Count: ${data}`
  }
}

admin_feed.onmessage = e => {
  let data = JSON.parse(e.data)
  console.log(data)
  if ('topic' in data && 'data' in data) {
    if (data['topic'] in message_handlers) {
      message_handlers[data['topic']](data['data'])
    }
  } else {
    console.error(`Invalid message in admin feed: ${data}`)
  }
}
// endregion
// endregion

function use(element) {
  fetch(`/api/use/${element.value}`, {
    method: "POST"
  }).then(res => {
    console.log(res)
  })
}

function setData(res) {
  if (typeof res !== 'string') {
    console.error('Couldn\'t set teams bcs raw WS data is not a string')
  }
  res = JSON.parse(res)
  if (!Array.isArray(res)) {
    console.error('Couldn\'t set teams bcs parsed WS data is not an array')
    return;
  }
  const chartElem = document.getElementById('chart');
  const chartLegendElem = document.getElementById('chart-legend');
  let highestCount = 0
  highestCount = res.find(t=>t.count > highestCount).count
  let colorIdx = 0;
  res.sort((a,b)=>a.team.id - b.team.id).forEach(t =>{
    // Search existing elem
    let chartValueEl = document.getElementById(t.team.id);
    if (!chartValueEl) {
      // create new
      chartValueEl = document.createElement('div');
      chartValueEl.id = t.team.id
      chartValueEl.classList.add('tui-chart-value', `${COLORS[colorIdx]}-168`);
      chartElem.append(chartValueEl)
      // Create legend name
      chartLegendEl = document.createElement('div');
      chartLegendEl.classList.add("tui-chart-legend");
      chartLegendEl.innerText = t.team.name
      chartLegendElem.append(chartLegendEl)
    }
    chartValueEl.style.height = `${(t.count / highestCount) * 100}%`
    chartValueEl.innerText = t.count;
    colorIdx = (colorIdx + 1) % COLORS.length
  })
}