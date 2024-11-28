import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

const App = () => {
  // Initialize state for CAN data
  const [canData, setCanData] = useState<any>(null);

  useEffect(() => {
    // listens for the 'can-message' event
    const handleCanData = (data: any) => {
      setCanData(data);
    };
    window.electron.onCanData((data) => {
      handleCanData(data);
    });

    // Cleanup listener when the component unmounts (optional)
    return () => {
      window.electron.removeCanDataListener(handleCanData);
    };
  }
); 

  return (
    <div>
      <h2>Hello from React!</h2>
      <p>CAN Data: {canData ? JSON.stringify(canData) : "No data received"}</p>
    </div>
  );
};

// Ensure that React renders the App to the DOM when the app is ready
const root = createRoot(document.body); // Ensure there's a div with id 'root' in index.html
root.render(<App />);
