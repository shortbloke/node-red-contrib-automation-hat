/**
 * Copyright 2018 Martin Rowan <martin@rowannet.co.uk>
 * Initial implementation Copyright 2016 Pimoroni Ltd
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 **/

module.exports = function(RED) {
    "use strict";

    function REDvDebug(message){
        if( RED.settings.verbose ) RED.log.info("AutomationHAT: " + message);
    }

    function REDvWarn(message){
        if( RED.settings.verbose ) RED.log.warn("AutomationHAT: " + message);
    }
    
    function REDvInfo(message){
        if( RED.settings.verbose ) RED.log.info("AutomationHAT: " + message);
    }

    var HAT = (function(){

        var fs = require("fs");
        var spawn = require("child_process").spawn;

        var cmd = __dirname+"/../library/automationhatlink";
        var hat = null;
        var allowExit = false;
        var reconnectTimer = null;
        var disconnectTimeout = null;
        var users = [];
        var msgObj = {};
        if ( !(fs.statSync(cmd).mode & 1) ) {
            throw "Error: '" + cmd + "' must be executable (755)";
        }

        process.env.PYTHONBUFFERED = 1;

        var connect = function() {
            if( reconnectTimer ) clearTimeout(reconnectTimer);

            reconnectTimer = null;
            allowExit = false;

            hat = spawn(cmd);

            users.forEach(function(node){
                node.status({fill:"green",shape:"dot",text:"Connected"});
            });

            function handleMessage(data){
                data = data.trim();
                if (data.length == 0) return;

                if (data.substring(0,5) == "DEBUG"){
                    REDvDebug(data);
                    return;
                }

                if (data.substring(0,5) == "ERROR"){
                    REDvWarn(data);
                    return;
                }

                if (data.substring(0,5) == "FATAL"){
                    throw "Error: " + data;
                }

                users.forEach(function(node){
                    if ( data.substring(0,6) == "analog" ){
                        var channel = data.substring(7,8);
                        var msg = data.split(":")[1];
                        var isForReader = data.split(":")[2] == "True";
                        if((!isForReader && node.send_analog) || (isForReader && node.send_reader_analog)){
                            if(msgObj && msgObj.req && msgObj.res){
                                node.send({topic:"automationhat/analog." + channel, payload:Number(msg), req : msgObj.req, res : msgObj.res});
                            } else {
                                node.send({topic:"automationhat/analog." + channel, payload:Number(msg)});
                            }
                        }
                    }
                    else if ( data.substring(0,5) == "input" ){
                        var channel = data.substring(6,7);
                        var msg = data.split(":")[1];
                        var isForReader = data.split(":")[2] == "True";
                        if((!isForReader && node.send_input) || (isForReader && node.send_reader_input)){
                            if(msgObj && msgObj.req && msgObj.req){
                                node.send({topic:"automationhat/input." + channel, payload:Number(msg), req : msgObj.req, res: msgObj.res});
                            } else {
                                node.send({topic:"automationhat/input." + channel, payload:Number(msg)});
                            }
                        }
                    }
                });

            }

            hat.stdout.on('data', function(data) {
                data = data.toString().trim();
                if (data.length == 0) return;

                var messages = data.split("\n");
                messages.forEach(function(message){
                    handleMessage(message);
                });
                //REDvInfo("Got Data: " + data + " :");

            });

            hat.stderr.on('data', function(data) {
                if (data = " UserWarning: Analog Four is not supported on Automation pHAT warnings.warn(\"Analog Four is not supported on Automation pHAT\")"){
                    // Ignore warning
                    // REDvWarn("Process Warning: "+data+" :");
                    return;
                }
                REDvWarn("Process Error: "+data+" :");

                hat.stdin.write("stop");
                hat.kill("SIGKILL");
            });

            hat.on('close', function(code) {
                REDvWarn("Process Exit: "+code+" :");

                hat = null;
                users.forEach(function(node){
                    node.status({fill:"red",shape:"circle",text:"Disconnected"});
                });

                if (!allowExit && !reconnectTimer){
                    REDvInfo("Attempting Reconnect");

                    reconnectTimer = setTimeout(function(){
                        connect();
                    },5000);
                }

            });

        }

        var disconnect = function(){
            disconnectTimeout = setTimeout(function(){
                if (hat !== null) {
                    allowExit = true;
                    hat.stdin.write("stop\n");
                    hat.kill("SIGKILL");
                }
            },3000);
            if (reconnectTimer) {
                clearTimeout(reconnedTimer);
            }

        }

        return {
            open: function(node){
                if (disconnectTimeout) clearTimeout(disconnectTimeout);
                if (!hat) connect();

                if(!reconnectTimer){
                    node.status({fill:"green",shape:"dot",text:"Connected"});
                }

                // REDvInfo("Adding node, input: " + (node.send_input ? "yes" : "no") + 
                //                    ", analog:" + (node.send_analog ? "yes" : "no") + 
                //                    ", threshold: " + node.send_threshold + 
                //                    ", ADC4 threshold: " + node.send_adc4_threshold);
                // REDvInfo("Adding node, reader: " + (node.reader_input ? "yes" : "no") + 
                //                    ", analog:" + (node.reader_analog ? "yes" : "no"));
                users.push(node);
            },
            close: function(node,done){
                users.splice(users.indexOf(node),1);
                
                REDvInfo("Removing node, count: " + users.length.toString());

                if(users.length === 0){
                    disconnect();
                }
            },
            send: function(msg, _msgObj){
                msgObj = _msgObj;
                if(hat) hat.stdin.write(msg+"\n");
            }
        }


    })();


    function AutomationHATIn(config) {
        RED.nodes.createNode(this,config);

        this.send_input = config.input;
        this.send_analog = config.analog;
        this.send_threshold = config.threshold;
        this.send_adc4_threshold = config.adc4_threshold

        var node = this;

        node.status({fill:"red",shape:"ring",text:"Disconnected"});

        REDvInfo("Initialising AutomationHATIn node");

        HAT.open(this);
        HAT.send("Set Analog Threshold:" + this.send_threshold)
        HAT.send("Set ADC4 Threshold:" + this.send_adc4_threshold)

        node.on("close", function(done) {
            HAT.close(this);
            done();
            REDvInfo("Node Closed");
        });
    }

    RED.nodes.registerType("rpi-automation-hat in",AutomationHATIn);

    function AutomationHATOut(config) {
        RED.nodes.createNode(this,config);
 
        var node = this;

        REDvInfo("Initialising AutomationHATOut node");

        HAT.open(this);

        node.on("input", function(msg) {
            if (typeof msg.payload === "number" || msg.payload === "on" || msg.payload == "off" || msg.payload == "toggle" || msg.payload == "enable" || msg.payload == "disable" || msg.payload == true || msg.payload == false){
                HAT.send(msg.topic + ":" + msg.payload.toString());
                REDvInfo("Sending Command: " + msg.topic + ":" + msg.payload.toString());
            }
        });

        node.on("close", function(done) {
            done();
        });
    }

    RED.nodes.registerType("rpi-automation-hat out",AutomationHATOut);

    function AutomationHATReader(config) {
        RED.nodes.createNode(this,config);

        this.send_reader_input = config.input;
        this.send_reader_analog = config.analog;

        var node = this;

        node.status({fill:"red",shape:"ring",text:"Disconnected"});

        REDvInfo("Initialising AutomationHATReader node");

        HAT.open(this);

        node.on("input", function(msg) {
            HAT.send("Reader:" + msg.payload.toString(), msg);
            REDvInfo("Sending Command: " + "Reader:" + msg.payload.toString());
        });

        node.on("close", function(done) {
            HAT.close(this);
            done();
            REDvInfo("Node Closed");
        });
    }

    RED.nodes.registerType("rpi-automation-hat reader",AutomationHATReader);

}
