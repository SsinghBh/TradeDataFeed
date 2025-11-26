from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BidAskQuote(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bidQ: str = None
    bidP: float = None
    askQ: str = None
    askP: float = None


class MarketLevel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bidAskQuote: list[BidAskQuote] = Field(default_factory=list)


class LTPC(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ltp: float = None
    ltt: str = None
    ltq: str = None
    cp: float = None


class OptionGreeks(BaseModel):
    model_config = ConfigDict(extra="ignore")

    delta: float = None
    theta: float = None
    gamma: float = None
    vega: float = None
    rho: float = None


class OHLCEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    interval: str = None
    open: float = None
    high: float = None
    low: float = None
    close: float = None
    vol: str = 0
    ts: str = None


class MarketOHLC(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ohlc: list[OHLCEntry] = Field(default_factory=list)


class MarketFF(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ltpc: Optional[LTPC] = None
    marketLevel: Optional[MarketLevel] = None
    optionGreeks: Optional[OptionGreeks] = None
    marketOHLC: Optional[MarketOHLC] = None

    atp: Optional[float] = None
    vtt: Optional[str] = None
    oi: Optional[int] = None
    iv: Optional[float] = None
    tbq: Optional[int] = None
    tsq: Optional[int] = None


class FullFeed(BaseModel):
    model_config = ConfigDict(extra="ignore")

    marketFF: Optional[MarketFF] = None


class InstrumentFeed(BaseModel):
    model_config = ConfigDict(extra="ignore")

    fullFeed: Optional[FullFeed] = None


class LiveFeed(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    feeds: dict[str, InstrumentFeed] = Field(default_factory=dict)
    currentTs: Optional[str] = None



if __name__ == "__main__":
    data = {'type': 'live_feed', 'feeds': {'NSE_EQ|INE531E01026': {'fullFeed': {'marketFF': {'ltpc': {'ltp': 248.5, 'ltt': '1757586501000', 'ltq': '16', 'cp': 248.58}, 'marketLevel': {'bidAskQuote': [{'bidQ': '63', 'bidP': 298.29, 'askQ': '200', 'askP': 240.3}, {'bidQ': '3000', 'bidP': 280.0, 'askQ': '201', 'askP': 243.61}, {'bidQ': '400', 'bidP': 265.0, 'askQ': '61', 'askP': 246.55}, {'bidQ': '43', 'bidP': 261.01, 'askQ': '61', 'askP': 247.1}, {'bidQ': '8014', 'askQ': '761'}]}, 'optionGreeks': {}, 'marketOHLC': {'ohlc': [{'interval': '1d', 'open': 251.0, 'high': 248.5, 'low': 248.5, 'close': 248.5, 'vol': '24147', 'ts': '1757615400000'}, {}]}, 'vtt': '24147', 'tbq': 153562.0, 'tsq': 357356.0}}, 'requestMode': 'full_d5'}}, 'currentTs': '1757648211290'}

    with open("rough.json", "w") as f:
        import json

        json.dump(data, f, indent=4)

    data_list = [LiveFeed(**data)]

    print(LiveFeed(**data).feeds['NSE_EQ|INE531E01026'])
    for data in data_list:
        for feed_name, feed_data in data.feeds.items():
            for interval_feed in feed_data.fullFeed.marketFF.marketOHLC.ohlc:
                row = {
                    'feed_name': feed_name,# if not REPLACE_INSTRUMENT_KEY_WITH_TRADE_SYMBOL else feed_data.fullFeed.get('trade_symbol', feed_name),
                    'interval': interval_feed.interval,
                    'Open': interval_feed.open,
                    'High': interval_feed.high,
                    'Low': interval_feed.low,
                    'Close': interval_feed.close,
                    'Volume': getattr(interval_feed, 'volume', 0),  # Assuming volume might not be present
                    'ts': interval_feed.ts
                }