import * as os from 'os';
import { ipcMain } from 'electron';
// import { LinuxCANInterface } from './can_linux';
// import { MockCANInterface } from './can_mock';

export interface ICANInterface {
    start(): void;
    stop(): void;
}

// Calls upon proper CAN Interface depending on OS
export function createCANInterface(channelName: string, win: Electron.BrowserWindow): ICANInterface {
    const platform = os.platform();

    if (platform === 'linux') {
        // eslint-disable-next-line @typescript-eslint/no-var-requires
        const can = require('socketcan');

        return new LinuxCANInterface(can, channelName);
    } else {
        return new MockCANInterface(channelName, win);
    }
}

// Linux-specific CAN Implementation
class LinuxCANInterface implements ICANInterface {
    private channel: any;

    constructor(private can: any, private channelName: string) {
        this.channel = this.can.createRawChannel(channelName, true);
    }

    start(): void {
        this.channel.start();
        console.log(`Linux CAN interface started on ${this.channel.ifname}`);

        
        this.channel.addListener('onMessage', (msg: any) => {
            const canMessage = {
                id: `0x${msg.id.toString(16)}`,
                data: msg.data.toString('hex'),
            };

            console.log(
                `CAN Message: ID=0x${msg.id.toString(16)}, Data=${msg.data.toString('hex')}`
            );
        });
    }

    stop(): void {
        this.channel.stop();
        console.log('Linux CAN interface stopped.');
    }
}

// Mock CAN implementation
class MockCANInterface implements ICANInterface {
    private intervalId: NodeJS.Timeout | null = null;

    constructor(private channelName: string, private win: Electron.BrowserWindow) {}

    start(): void {
        console.log(`Mock CAN interface started on ${this.channelName}`);
        this.intervalId = setInterval(() => {
            const dataLength = Math.floor(Math.random() * 9); 
            const data = [];
            for (let i = 0; i < dataLength; i++) {
              data.push(Math.floor(Math.random() * 256)); // Random byte between 0x00 and 0xFF
            }

            const dataString = data.map(byte => byte.toString(16).padStart(2, '0').toUpperCase()).join(' ');

            const simulatedMessage = { id: '0x123', data: dataString };
            // Send the simulated CAN message to the renderer process
            this.win.webContents.send('can-message', simulatedMessage);

            console.log(`Simulated CAN Message: ID=0x123,` + dataString);
        }, 10);
    }

    stop(): void {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        console.log('Mock CAN interface stopped.');
    }
}
