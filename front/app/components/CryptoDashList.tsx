import React, { useState, useEffect, useContext } from 'react';
import { CryptoContext } from '../context/CryptoContext';

// Structure des données pour une cryptomonnaie
interface Crypto {
    name: string;
    symbol: string;
    price: number;
    change: number;  // Variation du prix en %
    change24hUSD: number;
}

// Liste des cryptos pour la démonstration (vous pouvez remplacer ça par des données d'API)
const dummyCryptoData: Crypto[] = [
    { name: 'Bitcoin', symbol: 'BTC', price: 28000, change: 2.5 , change24hUSD: 300},
    { name: 'Ethereum', symbol: 'ETH', price: 1800, change: -1.2, change24hUSD:150 },
    { name: 'Binance Coin', symbol: 'BNB', price: 300, change: 0.4 , change24hUSD:29},
    { name: 'Ripple', symbol: 'XRP', price: 0.5, change: 3.1 , change24hUSD:100},
    { name: 'Cardano', symbol: 'ADA', price: 0.25, change: -0.8, change24hUSD:233 },
];

const CryptoListComponent: React.FC = () => {
    const [cryptos, setCryptos] = useState<Crypto[]>([]);
    const [selectedCrypto, setSelectedCrypto] = useState<Crypto | null>(null);
    let { symbol, setSymbol } = useContext(CryptoContext)
   
    // Simuler une récupération de données, ou utiliser une API ici
    useEffect(() => {
        const fetchCryptoData = async () => {
            const response = await fetch('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=5&page=1');
            const data = await response.json();
            const formattedData = data.map((crypto: any) => ({
                name: crypto.name,
                symbol: crypto.symbol.toUpperCase(),
                price: crypto.current_price,
                change: crypto.price_change_percentage_24h,
                change24hUSD: (crypto.current_price * crypto.price_change_percentage_24h) / 100
            }));
            console.log(formattedData)
            setCryptos(formattedData);
            setSelectedCrypto(formattedData[0]);  // Sélectionne la première crypto par défaut
        };
        setCryptos(dummyCryptoData);
        //fetchCryptoData();
    }, []);
    

    // Fonction pour gérer la sélection d'une crypto dans la liste
    const handleSelectCrypto = (crypto: Crypto) => {
        setSelectedCrypto(crypto);
        setSymbol(crypto.name.toLocaleLowerCase())
       
    };

    return (
        <div style={styles.container}>
            {/* Liste des cryptos */}
            <div style={styles.listContainer}>
                {cryptos.map((crypto, index) => (
                    <div
                        key={index}
                        style={{
                            ...styles.cryptoItem,
                            backgroundColor: selectedCrypto?.symbol === crypto.symbol ? '#f0f0f0' : 'white',
                        }}
                        onClick={() => handleSelectCrypto(crypto)}
                    >
                        <span style={styles.cryptoSymbol}>{crypto.symbol}</span>
                        <span style={styles.cryptoPrice}>${crypto.price.toFixed(2)}</span>
                        <span
                            style={{
                                ...styles.cryptoChange,
                                color: crypto.change >= 0 ? 'green' : 'red',
                            }}
                        >
                            {crypto.change > 0 ? `+${crypto.change}%` : `${crypto.change}%`}
                        </span>
                        <span
                            style={{
                                ...styles.cryptoChange,
                                color: crypto.change24hUSD.toFixed(2) >= 0 ? 'green' : 'red',
                            }}
                        >
                            {crypto.change24hUSD.toFixed(2) > 0 ? `+${crypto.change24hUSD.toFixed(2)}` : `${crypto.change24hUSD.toFixed(2)}`}
                        </span>
                    </div>
                ))}
            </div>

            {/* Détails de la crypto sélectionnée */}
            {selectedCrypto && (
                <div style={styles.detailsContainer}>
                    <h2>{selectedCrypto.name} ({selectedCrypto.symbol})</h2>
                    <p>Prix actuel : ${selectedCrypto.price.toFixed(2)}</p>
                    <p
                        style={{
                            color: selectedCrypto.change >= 0 ? 'green' : 'red',
                        }}
                    >
                        Variation : {selectedCrypto.change > 0 ? `+${selectedCrypto.change}%` : `${selectedCrypto.change}%`}
                    </p>
                </div>
            )}
        </div>
    );
};

// Styles en CSS-in-JS
const styles: { [key: string]: React.CSSProperties } = {
    container: {
        display: 'flex',
        flexDirection: 'column',
        padding: '10px',
        width: '400px',
        border: '1px solid #ddd',
        borderRadius: '8px',
        height:500
    },
    listContainer: {
        flex: 1,
        paddingRight: '10px',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
    },
    cryptoItem: {
        display: 'flex',
        justifyContent: 'space-between',
        padding: '10px',
        cursor: 'pointer',
        borderRadius: '5px',
        transition: 'background-color 0.2s ease-in-out',
    },
    cryptoSymbol: {
        fontWeight: 'bold',
        fontSize: '16px',
    },
    cryptoPrice: {
        fontSize: '14px',
        marginLeft: '10px',
    },
    cryptoChange: {
        fontSize: '14px',
        marginLeft: '10px',
    },
    detailsContainer: {
        flex: 1,
        borderTop:"1px solid black",
        paddingLeft: '10px',
        paddingTop:20,
        display: 'flex',
        flexDirection: 'column',
       
    },
};

export default CryptoListComponent;
