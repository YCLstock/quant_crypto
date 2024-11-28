# backend/scripts/test_historical_service.py

import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.historical.data_service import HistoricalDataService

class HistoricalServiceTester:
    def __init__(self):
        self.db: Session = SessionLocal()
        self.service = HistoricalDataService(self.db)
        self.results = []
        
    def run_test_suite(self):
        """運行完整測試套件"""
        try:
            print("Starting Historical Service Test Suite...")
            print("-" * 50)
            
            # 測試案例 1: 基本數據獲取
            self.test_historical_klines()
            
            # 測試案例 2: 波動率分析
            self.test_volatility_analysis()
            
            # 測試案例 3: 技術分析
            self.test_technical_analysis()
            
            # 生成測試報告
            self.generate_report()
            
        except Exception as e:
            print(f"Error in test suite: {e}")
        finally:
            self.db.close()

    def test_historical_klines(self):
        """測試歷史K線數據獲取"""
        test_cases = [
            {
                'symbol': 'BTCUSDT',
                'timeframe': '1h',
                'days': 7,
                'expected_count': 168
            },
            {
                'symbol': 'BTCUSDT',
                'timeframe': '4h',
                'days': 7,
                'expected_count': 42
            }
        ]
        
        for case in test_cases:
            print(f"\nTesting historical klines: {case['symbol']} {case['timeframe']}")
            
            start_time = datetime.now() - timedelta(days=case['days'])
            memory_before = psutil.Process().memory_info().rss / 1024 / 1024
            
            try:
                test_start = time.time()
                
                metrics = self.service._get_historical_metrics(
                    symbol=case['symbol'],
                    timeframe=case['timeframe'],
                    start_time=start_time
                )
                
                execution_time = time.time() - test_start
                memory_after = psutil.Process().memory_info().rss / 1024 / 1024
                memory_used = memory_after - memory_before
                
                result = {
                    'test_case': 'historical_klines',
                    'symbol': case['symbol'],
                    'timeframe': case['timeframe'],
                    'data_count': len(metrics),
                    'expected_count': case['expected_count'],
                    'execution_time': execution_time,
                    'memory_used': memory_used,
                    'status': 'success' if len(metrics) > 0 else 'warning',
                    'notes': []
                }
                
                if len(metrics) == 0:
                    result['notes'].append("No data returned")
                elif len(metrics) < case['expected_count']:
                    result['notes'].append(
                        f"Data incomplete: got {len(metrics)} records, "
                        f"expected {case['expected_count']}"
                    )
                
                if execution_time > 1.0:
                    result['notes'].append(
                        f"Slow execution: {execution_time:.2f} seconds"
                    )
                
                if memory_used > 100:
                    result['notes'].append(
                        f"High memory usage: {memory_used:.2f} MB"
                    )
                
                self.results.append(result)
                
                print(f"Status: {result['status']}")
                print(f"Records: {result['data_count']}")
                print(f"Execution time: {result['execution_time']:.2f}s")
                print(f"Memory used: {result['memory_used']:.2f}MB")
                
            except Exception as e:
                print(f"Error testing historical klines: {e}")
                self.results.append({
                    'test_case': 'historical_klines',
                    'symbol': case['symbol'],
                    'timeframe': case['timeframe'],
                    'status': 'error',
                    'error': str(e)
                })

    def test_volatility_analysis(self):
        """測試波動率分析"""
        print("\nTesting volatility analysis...")
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            test_start = time.time()
            
            analysis = self.service.analyze_volatility(
                symbol='BTCUSDT',
                timeframe='1h',
                start_time=datetime.now() - timedelta(days=7)
            )
            
            execution_time = time.time() - test_start
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            memory_used = memory_after - memory_before
            
            result = {
                'test_case': 'volatility_analysis',
                'execution_time': execution_time,
                'memory_used': memory_used,
                'status': 'success' if analysis else 'warning',
                'notes': []
            }
            
            if not analysis:
                result['notes'].append("No analysis results")
            else:
                required_keys = ['volatility_stats', 'regime_analysis', 'trend_analysis']
                missing_keys = [k for k in required_keys if k not in analysis]
                if missing_keys:
                    result['notes'].append(f"Missing keys: {missing_keys}")
            
            self.results.append(result)
            
            print(f"Status: {result['status']}")
            print(f"Execution time: {result['execution_time']:.2f}s")
            print(f"Memory used: {result['memory_used']:.2f}MB")
            
        except Exception as e:
            print(f"Error testing volatility analysis: {e}")
            self.results.append({
                'test_case': 'volatility_analysis',
                'status': 'error',
                'error': str(e)
            })

    def test_technical_analysis(self):
        """測試技術分析"""
        print("\nTesting technical analysis...")
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            test_start = time.time()
            
            analysis = self.service.generate_technical_analysis(
                symbol='BTCUSDT',
                timeframe='1h'
            )
            
            execution_time = time.time() - test_start
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            memory_used = memory_after - memory_before
            
            result = {
                'test_case': 'technical_analysis',
                'execution_time': execution_time,
                'memory_used': memory_used,
                'status': 'success' if analysis else 'warning',
                'notes': []
            }
            
            if not analysis:
                result['notes'].append("No analysis results")
            else:
                required_indicators = [
                    'trend_analysis', 
                    'technical_indicators',
                    'volatility_analysis'
                ]
                missing_indicators = [
                    i for i in required_indicators if i not in analysis
                ]
                if missing_indicators:
                    result['notes'].append(f"Missing indicators: {missing_indicators}")
            
            self.results.append(result)
            
            print(f"Status: {result['status']}")
            print(f"Execution time: {result['execution_time']:.2f}s")
            print(f"Memory used: {result['memory_used']:.2f}MB")
            
        except Exception as e:
            print(f"Error testing technical analysis: {e}")
            self.results.append({
                'test_case': 'technical_analysis',
                'status': 'error',
                'error': str(e)
            })

    def generate_report(self):
        """生成測試報告"""
        print("\nTest Report")
        print("=" * 50)
        
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r['status'] == 'success'])
        failed_tests = len([r for r in self.results if r['status'] == 'error'])
        warnings = len([r for r in self.results if r['status'] == 'warning'])
        
        print(f"\nTest Summary:")
        print(f"Total tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Warnings: {warnings}")
        
        print("\nDetailed Results:")
        for result in self.results:
            print(f"\nTest Case: {result['test_case']}")
            print(f"Status: {result['status']}")
            if result.get('execution_time'):
                print(f"Execution Time: {result['execution_time']:.2f}s")
            if result.get('memory_used'):
                print(f"Memory Used: {result['memory_used']:.2f}MB")
            if result.get('notes'):
                print("Notes:")
                for note in result['notes']:
                    print(f"- {note}")
            if result.get('error'):
                print(f"Error: {result['error']}")
        
        print("\nImprovement Suggestions:")
        self._generate_improvement_suggestions()

    def _generate_improvement_suggestions(self):
        """生成改進建議"""
        suggestions = []
        
        slow_operations = [r for r in self.results if r.get('execution_time', 0) > 1.0]
        if slow_operations:
            suggestions.append("Consider implementing Redis cache for slow operations:")
            for op in slow_operations:
                suggestions.append(f"- {op['test_case']}: {op['execution_time']:.2f}s")
        
        high_memory_ops = [r for r in self.results if r.get('memory_used', 0) > 100]
        if high_memory_ops:
            suggestions.append("Optimize memory usage for following operations:")
            for op in high_memory_ops:
                suggestions.append(f"- {op['test_case']}: {op['memory_used']:.2f}MB")
        
        incomplete_data = [
            r for r in self.results 
            if any('incomplete' in note.lower() for note in r.get('notes', []))
        ]
        if incomplete_data:
            suggestions.append("Improve data completeness checks for:")
            for data in incomplete_data:
                suggestions.append(f"- {data['test_case']}")
        
        for suggestion in suggestions:
            print(suggestion)

if __name__ == "__main__":
    tester = HistoricalServiceTester()
    tester.run_test_suite()