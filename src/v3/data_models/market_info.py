from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class MarketStatus(str, Enum):
    NORMAL_OPEN = "NORMAL_OPEN"       # Start of normal trading session
    NORMAL_CLOSE = "NORMAL_CLOSE"     # End of normal trading session
    PRE_OPEN_START = "PRE_OPEN_START" # Start of pre-market session
    PRE_OPEN_END = "PRE_OPEN_END"     # End of pre-market session
    CLOSING_START = "CLOSING_START"   # Start of closing phase
    CLOSING_END = "CLOSING_END"       # End of closing phase


class SegmentStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")

    NSE_COM: MarketStatus = Field(..., description="Commodity segment (NSE).")
    NCD_FO: MarketStatus = Field(..., description="NCD Futures & Options.")
    NSE_FO: MarketStatus = Field(..., description="NSE Futures & Options.")
    BSE_EQ: MarketStatus = Field(..., description="BSE Equity.")
    BCD_FO: MarketStatus = Field(..., description="BCD Futures & Options.")
    BSE_FO: MarketStatus = Field(..., description="BSE Futures & Options.")
    NSE_EQ: MarketStatus = Field(..., description="NSE Equity.")
    MCX_FO: MarketStatus = Field(..., description="MCX Futures & Options.")
    MCX_INDEX: MarketStatus = Field(..., description="MCX Index.")
    NSE_INDEX: MarketStatus = Field(..., description="NSE Index.")
    BSE_INDEX: MarketStatus = Field(..., description="BSE Index.")


class MarketInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    segmentStatus: SegmentStatus = Field(
        ..., description="Fixed set of segment statuses."
    )


class MarketInfoEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str = Field(..., description="Expected value: 'market_info'.")
    currentTs: str = Field(
        ..., description="Current timestamp in epoch milliseconds (as string)."
    )
    marketInfo: MarketInfo
