#!/usr/bin/env python3

# Copyright 2018 Martin Rowan <martin@rowannet.co.uk>
# Initial implementaiton Copyright 2016 Pimoroni Ltd

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import sys
from threading import Thread, Event
from queue import Queue, Empty

class NonBlockingStreamReader:

    def __init__(self, stream):
        '''
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        '''

        self._s = stream
        self._q = Queue()
        self._stop_event = Event()

        def _populateQueue(stream, queue, stop_event):
            '''
            Collect lines from 'stream' and put them in 'queue'.
            '''
            while not stop_event.is_set():
                line = stream.readline()
                if line:
                    queue.put(line)

        self._t = Thread(target = _populateQueue,
                args = (self._s, self._q, self._stop_event))
        self._t.daemon = True
        self._t.start() #start collecting lines from the stream

    def readline(self, timeout = None):
        try:
            return self._q.get(block = timeout is not None, timeout = timeout)
        except Empty:
            return None

    def stop(self):
        self._stop_event.set()


def millis():
    return int(round(time.time() * 1000))

def emit(message):
    sys.stdout.write(message + "\n")
    sys.stdout.flush()

def error(message):
    emit("ERROR: " + message)

def fatal(message):
    emit("FATAL: " + message)
    sys.exit(1)


try:
    import automationhat
except ImportError:
    fatal("Unable to import automationhat python library")

if automationhat.is_automation_hat() or automationhat.is_automation_phat():
    automationhat.enable_auto_lights(True)
else:
    fatal("automationHAT/automationPHAT not detected")

running = True

stdin = NonBlockingStreamReader(sys.stdin)

# pin_index = {'one':1, 'two':2, 'three':3, 'four':4}

# def handle_input(pin):
#     emit("input.{}:{}".format(pin_index[pin.name],pin.read()))

# automationhat.input.changed(handle_input)

# last_change = [0,0,0,0]
# last_value = [None,None,None,None]

# def handle_analog(analog, value):
#     global last_change, last_value

#     if millis() - last_change[analog.channel] > 1000 or last_value[analog.channel] is None or abs(last_value[analog.channel] - value) >= 0.1:
#         last_change[analog.channel] = millis()
#         last_value[analog.channel] = value
#         emit("analog.{}:{}".format(analog.channel,value))
# if explorerhat.has_analog:
#     explorerhat.analog.changed(handle_analog, 0.01)

relay_index = ['one','two','three']
output_index = ['one','two','three']
light_index = ['power','comms','warn']
on_values = ['1', 'on', 'enable', 'true']
off_values = ['0', 'off', 'disable', 'false']
toggle_values = ['toggle']

def handle_command(cmd):
    if cmd is not None:
        cmd = cmd.strip()

        if cmd.startswith("auto_lights") and ":" in cmd:
            # ToDo: Allow control of autolights for each of input, output, relay and analog
            cmd, data = cmd.split(":")
            # channel = cmd.split(".")[1]
            if data in on_values:
                automationhat.enable_auto_lights(True)
            else:
                automationhat.enable_auto_lights(False)
            return

        if cmd.startswith("relay") and ":" in cmd:
            cmd, data = cmd.split(":")
            channel = cmd.split(".")[1]

            if channel in relay_index:
                channel = relay_index.index(channel)
            else:
                channel = int(channel) - 1

            if channel < 0 or channel > 2:
                error("Invalid channel: " + str(channel))
                return

            if data in on_values:
                automationhat.relay[channel].on()
            elif data in off_values:
                automationhat.relay[channel].off()
            elif data in toggle_values:
                automationhat.relay[channel].toggle()
            else:
                error("Unhandled relay value: '" + data + "'")
            return

        if cmd.startswith("output") and ":" in cmd:
            cmd, data = cmd.split(":")
            channel = cmd.split(".")[1]

            if channel in output_index:
                channel = output_index.index(channel)
            else:
                channel = int(channel) - 1

            if channel < 0 or channel > 2:
                error("Invalid channel: " + str(channel))
                return

            if data in on_values:
                automationhat.output[channel].on()
            elif data in off_values:
                automationhat.output[channel].off()
            elif data in toggle_values:
                automationhat.output[channel].toggle()
            else:
                error("Unhandled output value: '" + data + "'")
            return

        if cmd.startswith("light.") and ":" in cmd:
            # ToDo: This doesn't support switching only specific lights associated with the input/output/relays.
            cmd, data = cmd.split(":")
            channel = cmd.split(".")[1]

            if channel in light_index:
                channel = light_index.index(channel)
            else:
                channel = int(channel) - 1

            if channel < 0 or channel > 2:
                error("Invalid channel: " + str(channel))
                return

            if data in on_values:
                automationhat.light[channel].on()
            elif data in off_values:
                automationhat.light[channel].off()
            elif data in toggle_values:
                automationhat.light[channel].toggle()
            else:
                error("Unhandled output value: '" + data + "'")
            return

        if cmd == "stop":
            stdin.stop()
            running = False


while running:
    cmd = stdin.readline(0.1)
    handle_command(cmd)
    time.sleep(0.001)

