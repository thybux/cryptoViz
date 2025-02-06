"use client"
import { Box, createTheme, ThemeProvider } from '@mui/material';
import React from 'react';
import CryptoNavBar from './CryptoNavBar';
import { CryptoProvider } from '../context/CryptoContext';
import Chart from './Chart';
import CryptoListComponent from './CryptoDashList';
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

const App = () => {
  return (
    <Box>
       <ThemeProvider theme={darkTheme}>
        <Box display={'flex'} padding={5} rowGap={2} columnGap={2}>
          <CryptoProvider>
            <Box style={{ width: '1000px', height: '1000px' }}>
              <Chart />
              <CryptoNavBar />
            </Box>
            <CryptoListComponent />
          </CryptoProvider>
        </Box>
       </ThemeProvider>
    </Box>
  );
};

export default App;