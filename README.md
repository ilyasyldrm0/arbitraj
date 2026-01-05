# Arbitraj Monitoring (Binance + Kraken)

Bu proje Binance ve Kraken borsalarından PUBLIC websocket akışları ile gerçek zamanlı fiyat verisi toplar, her 1 saniyede bir snapshot alıp SQLite DB’ye kaydeder ve iki yönlü arbitraj fırsatlarını event olarak kayıt altına alır. Streamlit tabanlı dashboard ile canlı izleme, raporlama ve CSV export sağlar.

## Özellikler
- Binance + Kraken websocket realtime veri (API key gerektirmez)
- 1 Hz snapshot kayıt
- İki yönlü arbitraj tespiti (Binance satış/Kraken alış ve tersi)
- Event başlangıç/kapanış kayıtları + max/avg net spread
- Streamlit çok sayfalı UI (Dashboard, History, Raw Data Explorer, Settings)
- CSV export (PDF export opsiyonel, ReportLab)
- SQLite + SQLAlchemy (ileride Postgres’e geçiş kolay)
- Reconnect + exponential backoff + ping/heartbeat
- Rotating log + console log
- Unit test (arbitrage hesapları)

## Dosya Ağacı
```
app/
  collectors/
    binance.py
    kraken.py
  core/
    arbitrage.py
    scheduler.py
    state.py
    symbol_mapping.py
  storage/
    db.py
    models.py
    repository.py
  scripts/
    init_db.py
    run_collector.py
  ui/
    app.py
    service_manager.py
    pages/
      1_Dashboard.py
      2_Arbitrage_History.py
      3_Raw_Data_Explorer.py
      4_Settings.py
  data/
    app.db
  exports/
  logs/
requirements.txt
README.md
.env.example
```

## Kurulum
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Veritabanı Oluşturma
```bash
python -m app.scripts.init_db
```

## Çalıştırma
> Projeyi **root klasöründen** çalıştırın. Bu sayede `app` paketi her ortamda doğru şekilde bulunur.

### 1) Streamlit UI
```bash
streamlit run app/ui/app.py
```

UI içinden **Dashboard** sayfasında **Start Monitoring** ile websocket collector başlatılır.

Windows tek tık çalıştırma:
```bat
run_ui.bat
```

Alternatif debug girişi:
```bash
python -m app.ui.app
```

### 2) CLI Collector (opsiyonel)
```bash
python -m app.scripts.run_collector
```

## Kullanım
1. **Settings** sayfasından watchlist, ücretler, threshold ve DB path’i ayarlayın.
2. **Dashboard** sayfasında Start Monitoring’e basın.
3. **Arbitrage History** ile event geçmişi ve CSV/PDF export alın.
4. **Raw Data Explorer** ile snapshot kayıtlarını inceleyin.

## Symbol Mapping
Kullanıcı UI’da `BTC/USDT` formatını seçer. İçeride:
- Binance: `BTCUSDT`
- Kraken: `XBT/USDT` (BTC yerine XBT)

`Settings` sayfasındaki JSON override ile mapping ekleyebilirsiniz:
```json
{
  "binance": {"BTC/USDT": "BTCUSDT"},
  "kraken": {"BTC/USDT": "XBT/USDT"}
}
```

## Test
```bash
pytest
```

## Notlar
- SQLite default path: `app/data/app.db`
- Log dosyası: `app/logs/app.log`
- CSV export çıktıları: `app/exports/`
