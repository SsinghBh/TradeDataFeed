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

    interval: str
    open: float
    high: float
    low: float
    close: float
    vol: str
    ts: str


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
    data = {"type":"live_feed","feeds":{"NSE_EQ|INE047A01021":{"fullFeed":{"marketFF":{"ltpc":{"ltp":2787.5,"ltt":"1757580454460","ltq":"10","cp":2785.8},"marketLevel":{"bidAskQuote":[{"bidQ":"45","bidP":2787.5,"askQ":"1","askP":2787.9},{"bidQ":"6","bidP":2787.3,"askQ":"24","askP":2788.4},{"bidQ":"44","bidP":2787.2,"askQ":"29","askP":2788.6},{"bidQ":"60","bidP":2787.1,"askQ":"5","askP":2788.7},{"bidQ":"21","bidP":2787.0,"askQ":"14","askP":2788.8}]},"optionGreeks":{},"marketOHLC":{"ohlc":[{"interval":"1d","open":2782.4,"high":2795.0,"low":2771.0,"close":2787.5,"vol":"118836","ts":"1757529000000"},{"interval":"I1","open":2786.5,"high":2789.5,"low":2786.5,"close":2789.0,"vol":"5848","ts":"1757580360000"}]},"atp":2784.62,"vtt":"118836","tbq":64839.0,"tsq":55703.0}},"marketFF":None,"ltpc":None,"marketLevel":None,"optionGreeks":None,"marketOHLC":None,"atp":None,"vtt":None,"oi":None,"tbq":None,"tsq":None,"currentTs":None}}}

    with open("rough.json", "w") as f:
        import json

        json.dump(data, f, indent=4)

    data_list = [LiveFeed(**data)]

    print(LiveFeed(**data).feeds['NSE_EQ|INE047A01021'])
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