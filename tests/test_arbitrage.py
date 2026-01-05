from __future__ import annotations

from app.core.arbitrage import ArbitrageEngine


def test_arbitrage_compute_net_pct() -> None:
    engine = ArbitrageEngine({"binance": 0.001, "kraken": 0.0026}, threshold_pct=0.2)
    result = engine.compute("BTC/USDT", "binance", 100.0, "kraken", 99.0)
    net = 100.0 * (1 - 0.001) - 99.0 * (1 + 0.0026)
    expected_pct = net / 99.0 * 100
    assert abs(result.net_pct - expected_pct) < 1e-6


def test_event_lifecycle() -> None:
    engine = ArbitrageEngine({"binance": 0.0, "kraken": 0.0}, threshold_pct=0.5)
    result = engine.compute("BTC/USDT", "binance", 101.0, "kraken", 100.0)
    action, state = engine.update_event_state(result)
    assert action == "start"
    assert state is not None

    result2 = engine.compute("BTC/USDT", "binance", 100.2, "kraken", 100.0)
    action, _ = engine.update_event_state(result2)
    assert action == "close"
