import React from 'react';
import StockTable from './components/StockTable';
import './App.css';

function App() {
  return (
    <div className="App">
      <h1>创业板股票列表</h1>
      <StockTable />
    </div>
  );
}

export default App;