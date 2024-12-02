import { useEffect, useState } from 'react';

const useWebSocket = (url: string) => {
  const [data, setData] = useState<any>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const socket = new WebSocket(url);

    socket.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    socket.onmessage = (event) => {
      const receivedData = JSON.parse(`{"id": 1190, "timestamp": 1732992177.400797, "data": 0}`);
      console.log("*",receivedData);
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

export default useWebSocket;
