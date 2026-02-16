const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

app.use(express.static('public'));

io.on('connection', (socket) => {
    console.log('User connected for interactive session');

    let executeProcess = null;

    socket.on('run-code', ({ code }) => {
        const filePath = path.join(__dirname, 'main.c');
        const binaryPath = path.join(__dirname, 'main.out');

        // 1. Save code
        fs.writeFileSync(filePath, code);

        // 2. Compile (Real-time feedback)
        socket.emit('output', '\x1b[1;34m[System] Compiling...\x1b[0m\n');
        const compile = spawn('gcc', [filePath, '-o', binaryPath]);

        compile.stderr.on('data', (data) => {
            socket.emit('output', `\x1b[1;31m[Error] ${data.toString()}\x1b[0m`);
        });

        compile.on('close', (exitCode) => {
            if (exitCode !== 0) {
                socket.emit('output', '\n\x1b[1;31m[System] Compilation Failed.\x1b[0m\n');
                return;
            }

            socket.emit('output', '\x1b[1;32m[System] Execution Started...\x1b[0m\n\n');

            // 3. Spawn Interactive Process
            executeProcess = spawn(binaryPath);

            // Stream Output character by character
            executeProcess.stdout.on('data', (data) => {
                socket.emit('output', data.toString());
            });

            executeProcess.stderr.on('data', (data) => {
                socket.emit('output', data.toString());
            });

            executeProcess.on('close', (code) => {
                socket.emit('output', `\n\n\x1b[1;34m[System] Process finished (Code ${code})\x1b[0m\n`);
                executeProcess = null;
                // Cleanup
                if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
                if (fs.existsSync(binaryPath)) fs.unlinkSync(binaryPath);
            });
        });
    });

    // Handle real-time input
    socket.on('input', (data) => {
        if (executeProcess && executeProcess.stdin.writable) {
            executeProcess.stdin.write(data);
        }
    });

    socket.on('disconnect', () => {
        if (executeProcess) executeProcess.kill();
    });
});

const PORT = 3000;
server.listen(PORT, () => {
    console.log(`Server: http://localhost:${PORT}`);
});
