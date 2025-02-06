import { Box } from '@mui/material';
import React from 'react';
import NavBar from './components/NavBar';
import CryptoChart from './components/CryptoChart';
import CryptoList from './components/CryptoList';
import CryptoNavBar from './components/CryptoNavBar';
import { CryptoProvider } from './context/CryptoContext';
import App from './components/App';

const page = () => {
  return (
    <Box>
      <NavBar />
      <Box>
       <App /> 
      </Box>
    </Box>
  );
};

export default page;