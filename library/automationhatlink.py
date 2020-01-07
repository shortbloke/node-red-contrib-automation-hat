#!/usr/bin/env python3

# Copyright 2018 Martin Rowan <martin@rowannet.co.uk>
# Initial implementation Copyright 2016 Pimoroni Ltd

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

channel_commands = ["light", "output", "relay"]
property_commands = [
    "auto_lights",
    "reader",
    "set analog threshold",
    "set adc4 threshold",
]
basic_commands = ["stop"]

channels = {"one": 1, "two": 2, "three": 3}

analog_inputs = {"one": 1, "two": 2, "three": 3}

lights = {"power": 1, "comms": 2, "warn": 3}
last_analog_value = [None, None, None, None, None]
input_last_value = [
    None,
    None,
    None,
    None,
]  # Four elements, since we don't use 0 just 1, 2 and 3.

on_values = ["1", "on", "enable", "true"]
off_values = ["0", "off", "disable", "false"]
toggle_values = ["toggle"]

running = True
# Thresholds set fairly high, as noisy when floating
threshold = 0.1
adc4_threshold = 0.1

device = "Unknown Device"


class NonBlockingStreamReader:
    def __init__(self, stream):
        """
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        """

        self._s = stream
        self._q = Queue()
        self._stop_event = Event()

        def _populateQueue(stream, queue, stop_event):
            """
            Collect lines from 'stream' and put them in 'queue'.
            """
            while not stop_event.is_set():
                line = stream.readline()
                if line:
                    queue.put(line)

        self._t = Thread(
            target=_populateQueue, args=(self._s, self._q, self._stop_event)
        )
        self._t.daemon = True
        self._t.start()  # start collecting lines from the stream

    def readline(self, timeout=None):
        try:
            return self._q.get(block=timeout is not None, timeout=timeout)
        except Empty:
            return None

    def stop(self):
        self._stop_event.set()


def emit(message):
    sys.stdout.write(message + "\n")
    sys.stdout.flush()


def debug(message):
    emit("DEBUG({}): {}".format(device, message))


def error(message):
    emit("ERROR({}): {}".format(device, message))


def fatal(message):
    emit("FATAL({}): {}".format(device, message))
    sys.exit(1)


def handle_input(buffered_input, forceEmit=False):
    global input_last_value
    for input_channel in channels:
        emit_message = False
        if input_last_value[channels[input_channel]] is None:
            emit_message = False  # Supress emit on 1st read/startup
        elif input_last_value[channels[input_channel]] != buffered_input[input_channel]:
            emit_message = True  # Value has changed
        if forceEmit:
            emit_message = True

        input_last_value[channels[input_channel]] = buffered_input[input_channel]
        if emit_message:
            emit(
                "input.{}:{}:{}".format(
                    channels[input_channel], buffered_input[input_channel], forceEmit
                )
            )


def handle_analog(analog, forceEmit=False):
    global last_analog_value
    global threshold

    for analog_channel in analog_inputs:
        emit_message = False
        channel = analog_inputs[analog_channel]
        value = analog[analog_channel]
        trigger_threshold = threshold
        if channel == 4:
            trigger_threshold = adc4_threshold
        if last_analog_value[channel] is None:
            emit_message = True  # Read on 1st read/startup
        elif (abs(last_analog_value[channel] - value)) >= trigger_threshold:
            emit_message = True  # Value has changed by more than the threshold
        if forceEmit:
            emit_message = True

        last_analog_value[channel] = value
        if emit_message:
            emit("analog.{}:{}:{}".format(channel, value, forceEmit))


def handle_command(command):
    global running
    global threshold
    global adc4_threshold

    if command is not None:
        cmd = command.strip().lower()
        debug("handle_command: {}".format(cmd))
        if ":" in cmd:
            cmd, data = cmd.split(":")

        if cmd in basic_commands:
            # Basic action command
            if cmd == "stop":
                stdin.stop()
                running = False
            return

        if cmd in property_commands:
            # Property setting command
            if cmd == "auto_lights":
                if data in on_values:
                    automationhat.enable_auto_lights(True)
                else:
                    automationhat.enable_auto_lights(False)
            elif cmd == "reader":
                handle_input(automationhat.input.read(), True)
                handle_analog(automationhat.analog.read(), True)
            elif (cmd == "set analog threshold") and (float(data) > 0):
                threshold = float(data)
            elif (cmd == "set adc4 threshold") and (float(data) > 0):
                adc4_threshold = float(data)
            return

        cmd, channel = cmd.split(".")
        if cmd in channel_commands:
            # Channel based command

            if channel in channels:
                channel = channels[channel]
            elif channel in lights:
                channel = lights[channel]
            else:
                channel = int(channel)
            index = channel - 1
            if cmd == "light":
                if automationhat.is_automation_phat():
                    error("Automation pHAT does not support lights")
                    return
                if (channel <= 0) or (channel > light_count):
                    error("Invalid light channel: {}".format(channel))
                    return
                if data in on_values:
                    automationhat.light[index].on()
                elif data in off_values:
                    automationhat.light[index].off()
                elif data in toggle_values:
                    automationhat.light[index].toggle()
                else:
                    error("Unhandled light value: '{}'".format(data))
            elif cmd == "output":
                if (channel <= 0) or (channel > output_count):
                    error("Invalid output channel: {}".format(channel))
                    return
                if data in on_values:
                    automationhat.output[index].on()
                elif data in off_values:
                    automationhat.output[index].off()
                elif data in toggle_values:
                    automationhat.output[index].toggle()
                else:
                    error("Unhandled output value: '{}'".format(data))
            elif cmd == "relay":
                if (channel <= 0) or (channel > relay_count):
                    if (automationhat.is_automation_phat()) and (channel > relay_count):
                        error("Automation pHAT only has a single relay")
                    else:
                        error("Invalid relay channel: {}".format(channel))
                    return
                if data in on_values:
                    automationhat.relay[index].on()
                elif data in off_values:
                    automationhat.relay[index].off()
                elif data in toggle_values:
                    automationhat.relay[index].toggle()
                else:
                    error("Unhandled relay value: '{}'".format(data))
            return
        else:
            # Invalid  command
            debug("Ignored command: {}".format(command))
            return


try:
    import automationhat
except ImportError:
    fatal("Unable to import automationhat python library")

if automationhat.is_automation_hat():
    device = "HAT"
    analog_inputs.update({"four": 4})
    relay_count = 3
    light_count = 3
    output_count = 3
    automationhat.enable_auto_lights(True)
    debug("Automation HAT Detected")
elif automationhat.is_automation_phat():
    device = "pHAT"
    relay_count = 1
    light_count = 0
    output_count = 3
    debug("Automation pHAT Detected")
else:
    fatal("Automation HAT/Automation pHAT not detected")

stdin = NonBlockingStreamReader(sys.stdin)

while running:
    cmd = stdin.readline(0.1)
    handle_command(cmd)
    handle_input(automationhat.input.read())
    handle_analog(automationhat.analog.read())
    time.sleep(0.001)
