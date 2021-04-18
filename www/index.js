const express = require('express');
const path = require('path');
const app = express();

app.use(express.urlencoded({
  extended: true
}))

//const hostname = "192.168.0.109";
//const fake_host = "0.0.0.0";
const port = 3000;
//add the router

app.set("view engine", "pug");
app.set("views", path.join(__dirname, "views"));

app.listen(port, function() {
  console.log('Listening to port:  ' + port);
});

// REST APIs
app.get('/', (req, res) => {
  let data = initialize_data();
  res.render('index', { data: data });
});


app.post('/', (req, res) => {
  // pass user's inst to simulator to get the next step cache
  let data = JSON.parse(req.body.data);
  if (data.inst["reset"] == 0) {
    data = update_setting(req.body);
  }else{
    data = update_data(req.body);
    console.log(JSON.stringify(data.inst, null,4));
  }

  res.render('index', { data: data });
});

app.post('/reset', (req, res) => {
  res.redirect('/');
});

function initialize_data(){
  inst0 = {
    "reset": 0,
    "num_cache": 3,
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
  return { inst: inst0, cache: cache0 };
}

function update_setting(req_body){
  let data = JSON.parse(req_body.data);
  data.inst["reset"] = 1;
  data.inst["cache_type"] = req_body["cache_type"];
  data.inst["num_cache"] = req_body["num_cache"];
  data.inst["cache_size"] = req_body["cache_size"];
  data.inst["line_size"] = req_body["line_size"];
  data.inst["mem_size"] = req_body["mem_size"];
  data.inst["cache_way"] = req_body["cache_way"];

  return data;
}

function update_data(req_body){
  let data = JSON.parse(req_body.data);
  let num_nodes = data.inst["num_cache"];
  if (num_nodes == 1){
    req_body.instr = [req_body.instr];
  }
  for(let i=0;i<num_nodes;i++){
    if(i==0){
      data.inst["node_0"] = parse_instruction(req_body.instr[i]);
    }else if(i==1){
      data.inst["node_1"] = parse_instruction(req_body.instr[i]);
    }else if(i==2){
      data.inst["node_2"] = parse_instruction(req_body.instr[i]);
    }
  }
  for (let i=0; i< data.inst["num_cache"];i++){
    let n_blocks = data.inst.cache_size/data.inst.line_size;
    let rnd_blockID = getRandomInt(n_blocks);
    data.cache[i]["cache"][rnd_blockID] = {
      "addr": 66,
      "tag": "001000",
      "index": null,
      "offset": "010",
      "protocol": "M"
    };
    data.cache[i]["LSR"] = rnd_blockID;
  }
  return data;
}

function parse_instruction(str){
  var array = str.split("\r\n");
  let parse_instr = [];
  array.forEach(code_line => parse_instr.push(code_line.split(" ")));
  return parse_instr;
}

function getRandomInt(max) {
  return Math.floor(Math.random() * max);
}

