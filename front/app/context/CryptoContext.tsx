import React, { createContext, useState, useContext, ReactNode } from 'react';

// Créer le type pour le contexte
type CryptoContextType = {
  symbol:string
  setSymbol: (newSymbol: string) => void;
};

// Créer le contexte avec des valeurs par défaut
export const CryptoContext = createContext<CryptoContextType | undefined>(undefined);

// Créer le fournisseur de contexte pour le `time`
export const CryptoProvider = ({ children }: { children: ReactNode }) => {
  const [symbol, setSymbol] = useState<string>('bitcoin'); // Valeur par défaut: 5 minutes
  return (
    <CryptoContext.Provider value={{ symbol, setSymbol }}>
      {children}
    </CryptoContext.Provider>
  );
};


