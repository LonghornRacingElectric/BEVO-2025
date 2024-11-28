// electron.d.ts

declare global {
    interface Window {
      electron: {
        onCanData: (callback: (data: any) => void) => void;
        removeCanDataListener: (callback: (data: any) => void) => void;

      };
    }
  }
  
  export {}; 
  