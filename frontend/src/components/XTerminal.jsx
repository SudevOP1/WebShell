import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { useEffect, useRef } from "react";
import "@xterm/xterm/css/xterm.css";

const terminal = new Terminal();
const fitAddon = new FitAddon();
const ws = new WebSocket("ws://localhost:8000/ws");

const XTerminal = () => {
  const terminalRef = useRef(null);
  const debug = true;
  let currentCmd = "";
  let enterPressedOnCmd = "";
  let firstResponseReceived = false;

  const debugLog = (...args) => {
    if (debug) {
      console.log(...args);
    }
  };

  // data received from backend
  useEffect(() => {
    ws.onopen = () => debugLog("ws connected");

    ws.onclose = () => debugLog("ws disconnected");

    ws.onerror = (e) => debugLog("ws error:", e);

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      debugLog("receive data:", data);

      // first response from backend received, now we can using terminal
      if (!firstResponseReceived) {
        firstResponseReceived = true;
      }

      // received output of cmd
      if (data.type === "output") {
        let output = data.output;

        // remove already typed cmd from output
        if (output.startsWith(enterPressedOnCmd)) {
          output = output.replace(enterPressedOnCmd + "\r\n", "");
        }

        terminal.write(output);
        enterPressedOnCmd = "";
        currentCmd = "";
        debugLog("currentCmd:", currentCmd);
        debugLog("enterPressedOnCmd:", enterPressedOnCmd);
      }
    };

    // closing ws here
    window.addEventListener("beforeunload", () => ws.close());
    return () => ws.close();
  }, []);

  useEffect(() => {
    if (!terminalRef.current) {
      return;
    }

    // load the fit addon
    terminal.loadAddon(fitAddon);
    terminal.open(terminalRef.current);

    // fit the terminal to container
    fitAddon.fit();

    // handle window resize
    const handleResize = () => {
      fitAddon.fit();
    };
    window.addEventListener("resize", handleResize);

    // handle key pressed before xterm handles them
    terminal.attachCustomKeyEventHandler((domEvent) => {
      // block keys not in allowedKeyCodes
      if (!allowedKeyCodes.includes(domEvent.keyCode)) {
        debugLog("Blocked key:", domEvent.keyCode);

        // return false to prevent xterm from handling this key
        return false;
      }

      // return true to let xterm handle allowed keys normally
      return true;
    });

    // key pressed
    terminal.onKey((e) => {
      const key = e.key;
      const domEvent = e.domEvent;

      // handle keys pressed only when:
      // (first response from backend received)
      // and (not waiting for output of previous cmd)
      if (!firstResponseReceived || enterPressedOnCmd.length !== 0) {
        return;
      }

      debugLog("key:", key);
      debugLog("domEvent.key:", domEvent.key);
      debugLog("keyCode:", domEvent.keyCode);

      // pressed enter key
      if (domEvent.keyCode === 13) {
        ws.send(
          JSON.stringify({
            type: "cmd",
            cmd: currentCmd.trim(),
          })
        );
        terminal.write("\r\n"); // in terminal, \r\n = newline (for windows)
        enterPressedOnCmd = currentCmd;
      }

      // pressed backspace key
      else if (domEvent.keyCode === 8) {
        if (currentCmd.length > 0) {
          currentCmd = currentCmd.slice(0, -1);
          terminal.write("\b \b"); // in terminal, \b \b = backspace
        }
      }

      // pressed regular character
      else {
        currentCmd += key;
        terminal.write(key);
      }

      debugLog("currentCmd", currentCmd);
      debugLog("enterPressedOnCmd:", enterPressedOnCmd);
    });

    return () => {
      window.removeEventListener("resize", handleResize);
      terminal.dispose();
    };
  }, [terminalRef, ws]);

  return <div ref={terminalRef} className="flex-1 w-full h-full"></div>;
};

export default XTerminal;

let numberKeyCodes = [
  48, // 0
  49, // 1
  50, // 2
  51, // 3
  52, // 4
  53, // 5
  54, // 6
  55, // 7
  56, // 8
  57, // 9
];

let alphabetKeyCodes = [
  65, // A
  66, // B
  67, // C
  68, // D
  69, // E
  70, // F
  71, // G
  72, // H
  73, // I
  74, // J
  75, // K
  76, // L
  77, // M
  78, // N
  79, // O
  80, // P
  81, // Q
  82, // R
  83, // S
  84, // T
  85, // U
  86, // V
  87, // W
  88, // X
  89, // Y
  90, // Z
];

let punctuationKeyCodes = [
  186, // ;
  187, // =
  188, // ,
  189, // -
  190, // .
  191, // /
  192, // `
  219, // [
  220, // \
  221, // ]
  222, // '
];

let arrowKeyCodes = [
  37, // left arrow
  38, // up arrow
  39, // right arrow
  40, // down arrow
];

let allowedKeyCodes = [
  8, // backspace
  13, // enter
  16, // shift
  20, // caps lock
  32, // space
];
allowedKeyCodes += numberKeyCodes;
allowedKeyCodes += alphabetKeyCodes;
allowedKeyCodes += punctuationKeyCodes;
// allowedKeyCodes += allowedKeyCodes;
