const express = require('express');
const path = require('path');
const app = express();

const { spawn } = require('child_process');

app.use(express.urlencoded({
  extended: true
}))

//const hostname = "192.168.0.109";
//const fake_host = "0.0.0.0";
const port = 3000;
//add the router

app.set("view engine", "pug");
app.set("views", path.join(__dirname, "views"));

app.listen(port, function () {
  console.log('Listening to port:  ' + port);
});

// REST APIs
app.get('/', (req, res) => {
  //let data = initialize_data();
  res.render('setting');
});

app.post('/set', (req, res) => {
  let data = initialize_data(req.body);
  res.render('index', { data: data });
});

app.post('/instruction', (req, res) => {
  console.log('/instruction');
  // update instruction
  let data = update_instruction(req.body);
  // simulate for the first step
  let simulator_program = find_simulator(data.inst["protocol_type"]);
  let simulator = spawn(simulator_program, [JSON.stringify(data.inst)]);
  simulator.stdout.on('data', function (d) {
    let parsed_d = JSON.parse(d.toString());
    data.cache = parsed_d.cache;
    data.inst = parsed_d.inst;
    data.inst['reset'] = 1;
    console.log(JSON.stringify(data));
    res.render('index', { data: data });
  });
});

app.post('/step', (req, res) => {
  console.log('/step');
  // call simulator to simulate one-step
  let data = JSON.parse(req.body.data);
  data.inst.run_node = req.body.run_node;
  data = parse_int(data);
  let simulator_program = find_simulator(data.inst["protocol_type"]);
  // spawn new child process to call the python script
  console.log(simulator_program);
  let simulator = spawn(simulator_program, [JSON.stringify(data.inst), JSON.stringify(data.cache)]);

  // collect data from script
  simulator.stdout.on('data', function (d) {
    let parsed_d = JSON.parse(d.toString());
    console.log(d.toString());
    data.cache = parsed_d.cache;
    data.inst = parsed_d.inst;
    res.render('index', { data: data });
  });
});

app.post('/reset', (req, res) => {
  res.redirect('/');
});

function update_setting(req_body) {
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

function update_instruction(req_body) {
  let data = JSON.parse(req_body.data);
  let num_nodes = data.inst["num_cache"];
  if (num_nodes == 1) {
    req_body.instr = [req_body.instr];
  }
  for (let i = 0; i < num_nodes; i++) {
    if (i == 0) {
      data.inst["node_0"] = parse_instruction(req_body.instr[i]);
    } else if (i == 1) {
      data.inst["node_1"] = parse_instruction(req_body.instr[i]);
    } else if (i == 2) {
      data.inst["node_2"] = parse_instruction(req_body.instr[i]);
    }
  }

  data.inst["run_node"] = req_body.run_node;
  data = parse_int(data);

  return data;
}

function parse_instruction(str) {
  var array = str.split("\r\n");
  let parse_instr = [];
  array.forEach(code_line => parse_instr.push(code_line.split(" ")));
  return parse_instr;
}

function parse_int(data) {
  data.inst["num_cache"] = parseInt(data.inst["num_cache"]);
  data.inst["cache_size"] = parseInt(data.inst["cache_size"]);
  data.inst["line_size"] = parseInt(data.inst["line_size"]);
  data.inst["mem_size"] = parseInt(data.inst["mem_size"]);
  data.inst["cache_way"] = parseInt(data.inst["cache_way"]);
  data.inst["reset"] = parseInt(data.inst["reset"]);
  data.inst["run_node"] = parseInt(data.inst["run_node"]);
  for (let i = 0; i < data.inst["num_cache"]; i++) {
    let node_id = "node_" + i;
    data.inst[node_id].forEach(function (part, index, theArray) {
      theArray[index][1] = parseInt(theArray[index][1]);
    });
  }
  return data;
}

function find_simulator(protocol) {
  switch (protocol) {
    case "snp_msi":
      return simulator_program = "./../MSI_snoop_simulator.py";
      break;
    case "snp_mesi":
      return simulator_program = "./../mesi.py";
      break;
    case "dir_msi":
      return simulator_program = "./../dir_based/ccsim_dir.py";
      break;
    default:
      return "";
  }
}

function getRandomInt(max) {
  return Math.floor(Math.random() * max);
}


function initialize_data(inst_body) {
  // Initialize instruction
  inst0 = inst_body;
  inst0["reset"] = 0;
  for (let i = 0; i < inst0.num_cache; i++) {
    if (i == 0) {
      inst0["node_0"] = [];
    } else if (i == 1) {
      inst0["node_1"] = [];
    } else if (i == 2) {
      inst0["node_2"] = [];
    }
  }
  // Initialize cache data
  cache0 = {};
  for (let i = 0; i < inst0.num_cache; i++) {
    cache0[i] = { "cache": {} };
    let n_blocks = inst0.cache_size / inst0.line_size;
    for (let j = 0; j < n_blocks; j++) {
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
  let n_mem = inst0.mem_size / inst0.line_size;
  cache0['dir'] = {'dict':{}};
  for (let k = 0; k < n_mem; k++) {
    cache0['dir']["dict"][k] = {
      "addr": null,
      "protocol": "I",
      "owner": null,
      "sharers": [],
      "ack_needed": 0,
      "ack_cnt": 0
    };
  }
  return { inst: inst0, cache: cache0 };
}


// function update_data(req_body) {
//   let data = JSON.parse(req_body.data);
//   let num_nodes = data.inst["num_cache"];
//   if (num_nodes == 1) {
//     req_body.instr = [req_body.instr];
//   }
//   for (let i = 0; i < num_nodes; i++) {
//     if (i == 0) {
//       data.inst["node_0"] = parse_instruction(req_body.instr[i]);
//     } else if (i == 1) {
//       data.inst["node_1"] = parse_instruction(req_body.instr[i]);
//     } else if (i == 2) {
//       data.inst["node_2"] = parse_instruction(req_body.instr[i]);
//     }
//   }
//   for (let i = 0; i < data.inst["num_cache"]; i++) {
//     let n_blocks = data.inst.cache_size / data.inst.line_size;
//     let rnd_blockID = getRandomInt(n_blocks);
//     data.cache[i]["cache"][rnd_blockID] = {
//       "addr": 66,
//       "tag": "001000",
//       "index": null,
//       "offset": "010",
//       "protocol": "M"
//     };
//     data.cache[i]["LSR"] = rnd_blockID;
//   }
//   return data;
// }

