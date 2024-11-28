import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowRight, TrendingUp, Activity, LineChart } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <div className="px-6 py-16 mx-auto text-center md:px-12 lg:px-24">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
          Crypto Analytics
          <span className="text-blue-600"> Platform</span>
        </h1>
        <p className="mt-6 text-lg leading-8 text-gray-600">
          Professional-grade cryptocurrency market analysis tools and real-time monitoring
        </p>
        <div className="flex items-center justify-center gap-4 mt-10">
          <a
            href="/market-analysis"
            className="inline-flex items-center gap-2 px-6 py-3 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-500"
          >
            Start Analysis
            <ArrowRight className="w-4 h-4" />
          </a>
        </div>
      </div>

      {/* Features Grid */}
      <div className="px-6 py-12 mx-auto max-w-7xl lg:px-8">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
          <Card className="transition-shadow hover:shadow-lg">
            <CardContent className="p-6">
              <TrendingUp className="w-12 h-12 mb-4 text-blue-600" />
              <h3 className="mb-2 text-xl font-bold">Market Analysis</h3>
              <p className="text-gray-600">
                Advanced technical analysis with real-time market indicators and trends
              </p>
            </CardContent>
          </Card>

          <Card className="transition-shadow hover:shadow-lg">
            <CardContent className="p-6">
              <Activity className="w-12 h-12 mb-4 text-blue-600" />
              <h3 className="mb-2 text-xl font-bold">Volatility Monitor</h3>
              <p className="text-gray-600">
                Track market volatility and identify trading opportunities
              </p>
            </CardContent>
          </Card>

          <Card className="transition-shadow hover:shadow-lg">
            <CardContent className="p-6">
              <LineChart className="w-12 h-12 mb-4 text-blue-600" />
              <h3 className="mb-2 text-xl font-bold">Technical Indicators</h3>
              <p className="text-gray-600">
                Comprehensive suite of technical indicators and chart patterns
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Market Stats */}
      <div className="px-6 py-12 bg-gray-50">
        <div className="mx-auto max-w-7xl">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
            <div className="text-center">
              <h3 className="text-2xl font-bold text-gray-900">24/7</h3>
              <p className="mt-2 text-gray-600">Real-time Monitoring</p>
            </div>
            <div className="text-center">
              <h3 className="text-2xl font-bold text-gray-900">100+</h3>
              <p className="mt-2 text-gray-600">Trading Pairs</p>
            </div>
            <div className="text-center">
              <h3 className="text-2xl font-bold text-gray-900">1M+</h3>
              <p className="mt-2 text-gray-600">Data Points Daily</p>
            </div>
            <div className="text-center">
              <h3 className="text-2xl font-bold text-gray-900">0.1s</h3>
              <p className="mt-2 text-gray-600">Update Frequency</p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="px-6 py-12 bg-white">
        <div className="mx-auto max-w-7xl">
          <p className="text-center text-gray-500">
            © 2024 Crypto Analytics. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}