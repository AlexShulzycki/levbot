// fetching market data goes here

const baseurl = "http://fapi.binance.com"
const contract = "PERPETUAL"
/**
 * How far back to we want to look
 */
const limit = 150
const timeframes = ["1m", "5m", "15m", "30m", "1h"]

/**
 * Fetches latest market data about a specific pair
 * @param pair
 */
export function getPair(pair:String){
    getTimeframe(pair, "1m")
}

/**
 * Fetches all timeframes, returns a promise
 * @param pair
 * @param timeframe
 */
function getTimeframe(pair:String, timeframe:String){
    // i will fucking killmuyself if there is no no-bullshit rest implementation
}