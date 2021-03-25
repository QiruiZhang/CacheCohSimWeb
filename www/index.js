const express = require('express');
const path = require('path');
let app = express();
app.set("view engine", "pug");
app.set("views", path.join(__dirname, "views"));

inst = {
  "reset": 0,
  "num_cache": 2,
  "cache_type": "d",
  "cache_size": 128,
  "line_size": 8,
  "mem_size": 512,
  "cache_way": 2,

  "node_0": [
    ["st", 66],
    ["ld", 66]
  ],

  "node_1": [
    ["st", 66],
    ["ld", 66]
  ]
};

cache = {
  "0": {
    "cache": {
      "0": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "1": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "2": {
        "addr": 66,
        "tag": "001000",
        "index": null,
        "offset": "010",
        "protocol": "I"
      },
      "3": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "4": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "5": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "6": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "7": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "8": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "9": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "10": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "11": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "12": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "13": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "14": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "15": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      }
    },
    "LSR": [
      "2"
    ]
  },
  "1": {
    "cache": {
      "0": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "1": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "2": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "3": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "4": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "5": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "6": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "7": {
        "addr": 66,
        "tag": "001000",
        "index": null,
        "offset": "010",
        "protocol": "M"
      },
      "8": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "9": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "10": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "11": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "12": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "13": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "14": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      },
      "15": {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      }
    },
    "LSR": [
      "7"
    ]
  }
}

data = { inst: inst, cache: cache };
app.get('/', (req, res) => {
  res.render('index', { data: data });
});

//add the router
app.listen(3000,  function() {
  console.log('Listening to port:  ' + 3000);
});