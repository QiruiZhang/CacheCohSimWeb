const express = require('express');
const path = require('path');
const app = express();

app.use(express.urlencoded({
  extended: true
}))

//const hostname = "192.168.0.109";
//const fake_host = "0.0.0.0";
const port = 3000;

app.set("view engine", "pug");
app.set("views", path.join(__dirname, "views"));

var data = { inst: "", cache: "" };
app.get('/', (req, res) => {
  initialize_data();
  res.render('index', { data: data });
});


app.post('/', (req, res) => {
  update_inst(req.body);
  res.render('index', { data: data });
});

app.post('/next', (req, res) => {
  update_data();
  res.render('index', { data: data });
});

app.post('/reset', (req, res) => {
  res.redirect('/');
});

//add the router
app.listen(port, function() {
  console.log('Listening to port:  ' + port);
});

function update_inst(new_inst){
  data.inst["reset"] = 1;
  data.inst["cache_type"] = new_inst["cache_type"];
  data.inst["num_cache"] = new_inst["num_cache"];
  data.inst["cache_size"] = new_inst["cache_size"];
  data.inst["line_size"] = new_inst["line_size"];
  data.inst["mem_size"] = new_inst["mem_size"];
  data.inst["cache_way"] = new_inst["cache_way"];
}

function initialize_data(){
  inst0 = {
    "reset": 0,
    "num_cache": 4,
    "cache_type": "d",
    "cache_size": 128,
    "line_size": 8,
    "mem_size": 512,
    "cache_way": 2,
  
    "node_0": [],
  
    "node_1": []
  };
  
  cache0 = {};
  for (let i = 0; i < inst0.num_cache; i++) {
    cache0[i] = {"cache":{}};
    let n_blocks = inst0.cache_size/inst0.line_size;
    for (let j=0; j< n_blocks; j++) {
      cache0[i]["cache"][j] = {
        "addr": null,
        "tag": null,
        "index": null,
        "offset": null,
        "protocol": "I"
      };
    }
    cache0[i]["LSR"] = [];
  }
  data = { inst: inst0, cache: cache0 };
}

function update_data(){
  for (let i=0; i< data.inst["num_cache"];i++){
    let n_blocks = data.inst.cache_size/data.inst.line_size;
    let rnd_blockID = getRandomInt(n_blcoks);
    data.cache[i]["cache"][rnd_blockID] = {
      "addr": 66,
      "tag": "001000",
      "index": null,
      "offset": "010",
      "protocol": "M"
    };
    data.cache[i]["LSR"] = rnd_blockID;
  }

/*
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
  */
  
  
  data = { inst: inst, cache: cache };
}

function getRandomInt(max) {
  return Math.floor(Math.random() * max);
}
