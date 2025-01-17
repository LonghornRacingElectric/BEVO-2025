"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const react_1 = require("react");
const useWebSocket = (url) => {
    const [data, setData] = (0, react_1.useState)(null);
    const [isConnected, setIsConnected] = (0, react_1.useState)(false);
    (0, react_1.useEffect)(() => {
        const socket = new WebSocket(url);
        socket.onopen = () => {
            console.log('WebSocket connected');
            setIsConnected(true);
        };
        socket.onmessage = (event) => {
            const receivedData = JSON.parse(`{"id": 1190, "timestamp": 1732992177.400797, "data": 0}`);
            console.log("*", receivedData);
            setData(null);
        };
        socket.onclose = () => {
            console.log('WebSocket disconnected');
            setIsConnected(false);
        };
        socket.onerror = (error) => {
            console.error('WebSocket error', error);
        };
        return () => {
            socket.close();
        };
    }, [url]);
    return { data, isConnected };
};
exports.default = useWebSocket;
