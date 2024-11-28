# backend/scripts/test_api.py

import asyncio
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, Optional

class ApiTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def test_endpoints(self):
        """測試主要端點並打印回應"""
        endpoints = {
            # 市場分析端點
            "market_analysis": {
                "url": "/api/v1/historical/market",
                "params": {
                    "symbol": "BTCUSDT",
                    "timeframe": "1h"
                }
            },
            # 波動率分析端點
            "volatility_regimes": {
                "url": "/api/v1/historical/volatility/regimes",
                "params": {
                    "symbol": "BTCUSDT",
                    "timeframe": "1h",
                    "lookback_days": 30
                }
            }
        }

        for name, config in endpoints.items():
            print(f"\nTesting {name}...")
            try:
                response = await self.client.get(
                    f"{self.base_url}{config['url']}", 
                    params=config['params']
                )
                print(f"Status: {response.status_code}")
                if response.is_success:
                    self._print_formatted_json(response.json())
                else:
                    print(f"Error: {response.text}")
            except Exception as e:
                print(f"Error testing {name}: {e}")

    def _print_formatted_json(self, data: Dict):
        """格式化打印 JSON 數據"""
        print(json.dumps(data, indent=2, ensure_ascii=False))

    async def close(self):
        await self.client.aclose()

async def main():
    tester = ApiTester()
    try:
        await tester.test_endpoints()
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main())