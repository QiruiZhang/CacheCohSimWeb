const express = require('express');
const path = require('path');
const app = express();

const { spawn } = require('child_process');

const port = 3000;

app.set("view engine", "pug");
app.set("views", path.join(__dirname, "views"));


app.listen(port, '0.0.0.0', function () {
  console.log('Listening to port:  ' + port);
});

app.get('/', (req, res) => {
  res.render('setting');
});

app.post('/set', (req, res) => {
  let data = initialize_data(req.body);
  res.render('index', { data: data });
});

app.post('/instruction', (req, res) => {
  let data = update_instruction(req.body);
  let simulator_program = find_simulator(data.inst["protocol_type"]);
  let simulator = spawn(simulator_program, [JSON.stringify(data.inst)]);
  simulator.stdout.on('data', function (d) {
    let parsed_d = JSON.parse(d.toString());
    data.cache = parsed_d.cache;
    data.inst = parsed_d.inst;
    data.inst['reset'] = 1;
    res.render('index', { data: data });
  });
});

app.post('/step', (req, res) => {
  let data = JSON.parse(req.body.data);
  data.inst.run_node = req.body.run_node;
  data = parse_int(data);
  let simulator_program = find_simulator(data.inst["protocol_type"]);
  console.log(simulator_program);
  let simulator = spawn(simulator_program, [JSON.stringify(data.inst), JSON.stringify(data.cache)], { stdio: 'pipe' });

  let bufferArray = [];
  simulator.stdout.on('data', (d) => {
    bufferArray.push(d)
  });

  simulator.stderr.on('data', (d) => {
    console.error('stderr: ${d}');
  });

  simulator.on('close', (code) => {
    console.log('child process exited with code ${code}');
    let dataBuffer = Buffer.concat(bufferArray);
    let parsed_d = JSON.parse(dataBuffer.toString());
    console.log(dataBuffer.toString());
    data.cache = parsed_d.cache;
    data.inst = parsed_d.inst;
    res.render('index', { data: data });
  });
});

app.post('/reset', (req, res) => {
  res.redirect('/');
});

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
  if (data.inst["run_node"] != 'all') {
    data.inst["run_node"] = parseInt(data.inst["run_node"]);
  }

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
  cache0['dir'] = { 'dict': {} };
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
