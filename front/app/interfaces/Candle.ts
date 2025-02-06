type UTCTimestamp = number;

export interface Candle {
    time: UTCTimestamp;
    open: number;
    high: number;
    low: number;
    close: number;
}

export interface GeneratedData {
    initialData: Candle[];
    realtimeUpdates: Candle[];
}
