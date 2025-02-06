import React, { useState, useEffect, useRef, useContext } from 'react';
import { createChart, IChartApi, CandlestickSeriesApi, LineSeriesApi, UTCTimestamp } from 'lightweight-charts';
import { CryptoContext } from '../context/CryptoContext';

interface Candle {
    time: UTCTimestamp;
    open: number;
    high: number;
    low: number;
    close: number;
}

const timeframes = {
    '1m': '1',
    '5m': '5',
    '15m': '15',
    '1h': '60',
};

// Configurations des indicateurs
const indicators = {
    MA: {
        periods: [20, 50, 200],
        colors: ['#ff6b6b', '#4ecdc4', '#45b7d1'],
    },
    Bollinger: {
        period: 20,
        stdDev: 2,
        color: '#9775fa',
    },
};

// Récupérer le dernier prix
const latestPrice = async (crypto: string) => {
    let result = await fetch('http://10.18.206.239:6060/crypto/latest/' + crypto);
    let data = await result.json();
    data.ohlc.time = (new Date(data.timestamp).getTime() / 1000) as UTCTimestamp;
    const newCandle: Candle = data.ohlc;
    return newCandle;
};

// Récupérer les données historiques
const historyPrice = async (crypto: string, timeframe: string) => {
    let result = await fetch(`http://10.18.206.239:6060/crypto/history/${crypto}?timeframe=${timeframe}`);
    let data = await result.json();
    return data.history.map((candle: any) => ({
        time: (new Date(candle.timestamp).getTime() / 1000) as UTCTimestamp,
        open: candle.ohlc.open,
        high: candle.ohlc.high,
        low: candle.ohlc.low,
        close: candle.ohlc.close,
    }));
};

// Calculer la moyenne mobile (MA)
const calculateMA = (data: Candle[], period: number) => {
    const maData = [];
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            maData.push({ time: data[i].time, value: NaN });
            continue;
        }
        const slice = data.slice(i - period + 1, i + 1);
        const sum = slice.reduce((acc, curr) => acc + curr.close, 0);
        const ma = sum / period;
        maData.push({ time: data[i].time, value: ma });
    }
    return maData;
};

// Calculer les bandes de Bollinger
const calculateBollingerBands = (data: Candle[], period: number, stdDevFactor: number) => {
    const maData = calculateMA(data, period);
    const bands = {
        middle: maData,
        upper: [],
        lower: []
    };

    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            bands.upper.push({ time: data[i].time, value: NaN });
            bands.lower.push({ time: data[i].time, value: NaN });
            continue;
        }

        const slice = data.slice(i - period + 1, i + 1);
        const mean = maData[i].value;
        const variance = slice.reduce((acc, curr) => acc + Math.pow(curr.close - mean, 2), 0) / period;
        const stdDev = Math.sqrt(variance);

        bands.upper.push({ time: data[i].time, value: mean + stdDevFactor * stdDev });
        bands.lower.push({ time: data[i].time, value: mean - stdDevFactor * stdDev });
    }

    return bands;
};

const ChartComponent: React.FC = () => {
    let {symbol} = useContext(CryptoContext)
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const seriesRef = useRef<CandlestickSeriesApi | null>(null);
    const maSeriesRefs = useRef<LineSeriesApi[]>([]);
    const bollingerSeriesRefs = useRef<{
        upper: LineSeriesApi | null;
        middle: LineSeriesApi | null;
        lower: LineSeriesApi | null;
    }>({ upper: null, middle: null, lower: null });

    const [selectedTimeframe, setSelectedTimeframe] = useState<'1m' | '5m' | '15m' | '1h'>('1m');
    const [showMA, setShowMA] = useState<boolean>(false);
    const [showBollinger, setShowBollinger] = useState<boolean>(false);

    // Fonction pour mettre à jour une bougie existante
    const updateCandle = (candle: Candle, newValue: number): Candle => ({
        time: candle.time,
        close: newValue,
        open: candle.open,
        low: Math.min(candle.low, newValue),
        high: Math.max(candle.high, newValue),
    });
    const initializeChart = async () => {
        const historicalData = await historyPrice(symbol, selectedTimeframe);
        seriesRef.current?.setData(historicalData);

        // Mettre à jour les indicateurs
        if (showMA) {
            indicators.MA.periods.forEach((period, index) => {
                const maData = calculateMA(historicalData, period);
                maSeriesRefs.current[index]?.setData(maData);
            });
        }

        if (showBollinger) {
            const bollingerData = calculateBollingerBands(
                historicalData,
                indicators.Bollinger.period,
                indicators.Bollinger.stdDev
            );
            bollingerSeriesRefs.current.upper?.setData(bollingerData.upper);
            bollingerSeriesRefs.current.middle?.setData(bollingerData.middle);
            bollingerSeriesRefs.current.lower?.setData(bollingerData.lower);
        }

        chartRef.current?.timeScale().fitContent();
        let count = 0
        // Gérer les mises à jour en temps réel
        const intervalId = setInterval(async () => {
            count++
            const latestCandle = await latestPrice(symbol);
            const lastCandle = historicalData[historicalData.length - 1];
            console.log(latestCandle)
            console.log(historicalData)
            if (count < 5) {
                // Mettre à jour la dernière bougie
                const updatedCandle = updateCandle(lastCandle, latestCandle.close);
                try {
                    
                    seriesRef.current?.update(updatedCandle);
                } catch (error) {
                    
                }
            } else {
                // Ajouter une nouvelle bougie
                seriesRef.current?.update(latestCandle);
                historicalData.push(latestCandle);
                count = 0
            }
            

            // Mettre à jour les indicateurs
            if (showMA) {
                indicators.MA.periods.forEach((period, index) => {
                    const maData = calculateMA(historicalData, period);
                    maSeriesRefs.current[index]?.setData(maData);
                });
            }

            if (showBollinger) {
                const bollingerData = calculateBollingerBands(
                    historicalData,
                    indicators.Bollinger.period,
                    indicators.Bollinger.stdDev
                );
                bollingerSeriesRefs.current.upper?.setData(bollingerData.upper);
                bollingerSeriesRefs.current.middle?.setData(bollingerData.middle);
                bollingerSeriesRefs.current.lower?.setData(bollingerData.lower);
            }
        }, 10000); // Mise à jour toutes les 10 secondes
        return () => clearInterval(intervalId);
    };
    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chartOptions = {
            layout: {
                textColor: 'black',
                background: { type: 'solid', color: 'white' },
            },
            height: 500,
            watermark: {
                visible: false,
            },
        };

        const chart = createChart(chartContainerRef.current, chartOptions);
        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: true,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });

        chartRef.current = chart;
        seriesRef.current = candlestickSeries;

        // Initialiser les séries MA
        maSeriesRefs.current = indicators.MA.periods.map((period, index) =>
            chart.addLineSeries({
                color: indicators.MA.colors[index],
                lineWidth: 2,
                visible: showMA,
            })
        );

        // Initialiser les séries Bollinger
        const bollingerUpper = chart.addLineSeries({
            color: indicators.Bollinger.color,
            lineWidth: 1,
            lineStyle: 2,
            visible: showBollinger,
        });
        const bollingerMiddle = chart.addLineSeries({
            color: indicators.Bollinger.color,
            lineWidth: 2,
            visible: showBollinger,
        });
        const bollingerLower = chart.addLineSeries({
            color: indicators.Bollinger.color,
            lineWidth: 1,
            lineStyle: 2,
            visible: showBollinger,
        });

        bollingerSeriesRefs.current = {
            upper: bollingerUpper,
            middle: bollingerMiddle,
            lower: bollingerLower,
        };

        return () => {
            chart.remove();
        };
    }, []);

    useEffect(() => {
        
        if (!chartRef.current || !seriesRef.current) return;

        

        initializeChart();
    }, [selectedTimeframe, showMA, showBollinger,symbol]);

    // Gérer la visibilité des MA
    useEffect(() => {
        maSeriesRefs.current.forEach(series => {
            series?.applyOptions({ visible: showMA });
        });
    }, [showMA]);

    // Gérer la visibilité des Bollinger Bands
    useEffect(() => {
        Object.values(bollingerSeriesRefs.current).forEach(series => {
            series?.applyOptions({ visible: showBollinger });
        });
    }, [showBollinger]);

    return (
        <div>
            <div style={styles.controlsContainer}>
                <div style={styles.timeframeContainer}>
                    {Object.keys(timeframes).map((tf, index) => (
                        <button
                            key={index}
                            style={{
                                ...styles.button,
                                backgroundColor: selectedTimeframe === tf ? '#ddd' : '#fff',
                            }}
                            onClick={() => setSelectedTimeframe(tf as '1m' | '5m' | '15m' | '1h')}
                        >
                            {tf}
                        </button>
                    ))}
                </div>
                <div style={styles.indicatorsContainer}>
                    <button
                        style={{
                            ...styles.button,
                            backgroundColor: showMA ? '#ddd' : '#fff',
                        }}
                        onClick={() => setShowMA(!showMA)}
                    >
                        MA
                    </button>
                    <button
                        style={{
                            ...styles.button,
                            backgroundColor: showBollinger ? '#ddd' : '#fff',
                        }}
                        onClick={() => setShowBollinger(!showBollinger)}
                    >
                        Bollinger
                    </button>
                </div>
            </div>
            <div ref={chartContainerRef} style={{ position: 'relative', width: '100%', height: '400px' }} />
        </div>
    );
};

const styles: { [key: string]: React.CSSProperties } = {
    controlsContainer: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '10px',
    },
    timeframeContainer: {
        display: 'flex',
        gap: '5px',
    },
    indicatorsContainer: {
        display: 'flex',
        gap: '5px',
    },
    button: {
        padding: '8px 16px',
        fontWeight: 'bold',
        cursor: 'pointer',
        borderRadius: '5px',
        border: '1px solid #ddd',
        backgroundColor: 'white',
    },
};

export default ChartComponent;