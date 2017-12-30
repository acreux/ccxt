# -*- coding: utf-8 -*-

from ccxt.async.base.exchange import Exchange
import base64
import hashlib
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import NotSupported
from ccxt.base.errors import OrderNotFound


class btcmarkets (Exchange):

    def describe(self):
        return self.deep_extend(super(btcmarkets, self).describe(), {
            'id': 'btcmarkets',
            'name': 'BTC Markets',
            'countries': 'AU',  # Australia
            'rateLimit': 1000,  # market data cached for 1 second(trades cached for 2 seconds)
            'hasCORS': False,
            'hasFetchOrder': True,
            'hasFetchOrders': True,
            'hasFetchClosedOrders': True,
            'hasFetchOpenOrders': True,
            'hasFetchMyTrades': True,
            'has': {
                'fetchOrder': True,
                'fetchOrders': True,
                'fetchClosedOrders': 'emulated',
                'fetchOpenOrders': True,
                'fetchMyTrades': True,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/29142911-0e1acfc2-7d5c-11e7-98c4-07d9532b29d7.jpg',
                'api': 'https://api.btcmarkets.net',
                'www': 'https://btcmarkets.net/',
                'doc': 'https://github.com/BTCMarkets/API',
            },
            'api': {
                'public': {
                    'get': [
                        'market/{id}/tick',
                        'market/{id}/orderbook',
                        'market/{id}/trades',
                    ],
                },
                'private': {
                    'get': [
                        'account/balance',
                        'account/{id}/tradingfee',
                    ],
                    'post': [
                        'fundtransfer/withdrawCrypto',
                        'fundtransfer/withdrawEFT',
                        'order/create',
                        'order/cancel',
                        'order/history',
                        'order/open',
                        'order/trade/history',
                        'order/createBatch',  # they promise it's coming soon...
                        'order/detail',
                    ],
                },
            },
            'markets': {
                'BTC/AUD': {'id': 'BTC/AUD', 'symbol': 'BTC/AUD', 'base': 'BTC', 'quote': 'AUD', 'maker': 0.0085, 'taker': 0.0085},
                'LTC/AUD': {'id': 'LTC/AUD', 'symbol': 'LTC/AUD', 'base': 'LTC', 'quote': 'AUD', 'maker': 0.0085, 'taker': 0.0085},
                'ETH/AUD': {'id': 'ETH/AUD', 'symbol': 'ETH/AUD', 'base': 'ETH', 'quote': 'AUD', 'maker': 0.0085, 'taker': 0.0085},
                'ETC/AUD': {'id': 'ETC/AUD', 'symbol': 'ETC/AUD', 'base': 'ETC', 'quote': 'AUD', 'maker': 0.0085, 'taker': 0.0085},
                'XRP/AUD': {'id': 'XRP/AUD', 'symbol': 'XRP/AUD', 'base': 'XRP', 'quote': 'AUD', 'maker': 0.0085, 'taker': 0.0085},
                'BCH/AUD': {'id': 'BCH/AUD', 'symbol': 'BCH/AUD', 'base': 'BCH', 'quote': 'AUD', 'maker': 0.0085, 'taker': 0.0085},
                'LTC/BTC': {'id': 'LTC/BTC', 'symbol': 'LTC/BTC', 'base': 'LTC', 'quote': 'BTC', 'maker': 0.0022, 'taker': 0.0022},
                'ETH/BTC': {'id': 'ETH/BTC', 'symbol': 'ETH/BTC', 'base': 'ETH', 'quote': 'BTC', 'maker': 0.0022, 'taker': 0.0022},
                'ETC/BTC': {'id': 'ETC/BTC', 'symbol': 'ETC/BTC', 'base': 'ETC', 'quote': 'BTC', 'maker': 0.0022, 'taker': 0.0022},
                'XRP/BTC': {'id': 'XRP/BTC', 'symbol': 'XRP/BTC', 'base': 'XRP', 'quote': 'BTC', 'maker': 0.0022, 'taker': 0.0022},
                'BCH/BTC': {'id': 'BCH/BTC', 'symbol': 'BCH/BTC', 'base': 'BCH', 'quote': 'BTC', 'maker': 0.0022, 'taker': 0.0022},
            },
        })

    async def fetch_balance(self, params={}):
        await self.load_markets()
        balances = await self.privateGetAccountBalance()
        result = {'info': balances}
        for b in range(0, len(balances)):
            balance = balances[b]
            currency = balance['currency']
            multiplier = 100000000
            total = float(balance['balance'] / multiplier)
            used = float(balance['pendingFunds'] / multiplier)
            free = total - used
            account = {
                'free': free,
                'used': used,
                'total': total,
            }
            result[currency] = account
        return self.parse_balance(result)

    async def fetch_order_book(self, symbol, params={}):
        await self.load_markets()
        market = self.market(symbol)
        orderbook = await self.publicGetMarketIdOrderbook(self.extend({
            'id': market['id'],
        }, params))
        timestamp = orderbook['timestamp'] * 1000
        return self.parse_order_book(orderbook, timestamp)

    def parse_ticker(self, ticker, market=None):
        timestamp = ticker['timestamp'] * 1000
        symbol = None
        if market:
            symbol = market['symbol']
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': None,
            'low': None,
            'bid': float(ticker['bestBid']),
            'ask': float(ticker['bestAsk']),
            'vwap': None,
            'open': None,
            'close': None,
            'first': None,
            'last': float(ticker['lastPrice']),
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': float(ticker['volume24h']),
            'quoteVolume': None,
            'info': ticker,
        }

    async def fetch_ticker(self, symbol, params={}):
        await self.load_markets()
        market = self.market(symbol)
        ticker = await self.publicGetMarketIdTick(self.extend({
            'id': market['id'],
        }, params))
        return self.parse_ticker(ticker, market)

    def parse_trade(self, trade, market):
        timestamp = trade['date'] * 1000
        return {
            'info': trade,
            'id': str(trade['tid']),
            'order': None,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': market['symbol'],
            'type': None,
            'side': None,
            'price': trade['price'],
            'amount': trade['amount'],
        }

    async def fetch_trades(self, symbol, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        response = await self.publicGetMarketIdTrades(self.extend({
            # 'since': 59868345231,
            'id': market['id'],
        }, params))
        return self.parse_trades(response, market, since, limit)

    async def create_order(self, symbol, type, side, amount, price=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        multiplier = 100000000  # for price and volume
        # does BTC Markets support market orders at all?
        orderSide = 'Bid' if (side == 'buy') else 'Ask'
        order = self.ordered({
            'currency': market['quote'],
        })
        order['currency'] = market['quote']
        order['instrument'] = market['base']
        order['price'] = int(price * multiplier)
        order['volume'] = int(amount * multiplier)
        order['orderSide'] = orderSide
        order['ordertype'] = self.capitalize(type)
        order['clientRequestId'] = str(self.nonce())
        response = await self.privatePostOrderCreate(order)
        return {
            'info': response,
            'id': str(response['id']),
        }

    async def cancel_orders(self, ids):
        await self.load_markets()
        return await self.privatePostOrderCancel({'order_ids': ids})

    async def cancel_order(self, id, symbol=None, params={}):
        await self.load_markets()
        return await self.cancel_orders([id])

    def parse_my_trade(self, trade, market):
        multiplier = 100000000
        timestamp = trade['creationTime']
        side = 'buy' if (trade['side'] == 'Bid') else 'sell'
        # BTCMarkets always charge in AUD for AUD-related transactions.
        currency = market['quote'] if (market['quote'] == 'AUD') else market['base']
        return {
            'info': trade,
            'id': str(trade['id']),
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': market['symbol'],
            'type': None,
            'side': side,
            'price': trade['price'] / multiplier,
            'fee': {
                'currency': currency,
                'cost': trade['fee'] / multiplier,
            },
            'amount': trade['volume'] / multiplier,
        }

    def parse_my_trades(self, trades, market=None, since=None, limit=None):
        result = []
        for i in range(0, len(trades)):
            trade = self.parse_my_trade(trades[i], market)
            result.append(trade)
        return result

    def parse_order(self, order, market=None):
        multiplier = 100000000
        side = 'buy' if (order['orderSide'] == 'Bid') else 'sell'
        type = 'limit' if (order['ordertype'] == 'Limit') else 'market'
        timestamp = order['creationTime']
        if not market:
            market = self.market(order['instrument'] + "/" + order['currency'])
        status = 'open'
        if order['status'] == 'Failed' or order['status'] == 'Cancelled' or order['status'] == 'Partially Cancelled' or order['status'] == 'Error':
            status = 'canceled'
        elif order['status'] == "Fully Matched" or order['status'] == "Partially Matched":
            status = 'closed'
        price = self.safe_float(order, 'price') / multiplier
        amount = self.safe_float(order, 'volume') / multiplier
        remaining = self.safe_float(order, 'openVolume', 0.0) / multiplier
        filled = amount - remaining
        cost = price * amount
        trades = self.parse_my_trades(order['trades'], market)
        result = {
            'info': order,
            'id': str(order['id']),
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': market['symbol'],
            'type': type,
            'side': side,
            'price': price,
            'cost': cost,
            'amount': amount,
            'filled': filled,
            'remaining': remaining,
            'status': status,
            'trades': trades,
            'fee': None,
        }
        return result

    async def fetch_order(self, id, symbol=None, params={}):
        await self.load_markets()
        ids = [id]
        response = await self.privatePostOrderDetail(self.extend({
            'orderIds': ids,
        }, params))
        numOrders = len(response['orders'])
        if numOrders < 1:
            raise OrderNotFound(self.id + ' No matching order found: ' + id)
        order = response['orders'][0]
        return self.parse_order(order)

    async def prepare_history_request(self, market, since=None, limit=None):
        request = self.ordered({
            'currency': market['quote'],
            'instrument': market['base'],
        })
        if limit:
            request['limit'] = limit
        else:
            request['limit'] = 100
        if since:
            request['since'] = since
        else:
            request['since'] = 0
        return request

    async def fetch_orders(self, symbol=None, since=None, limit=None, params={}):
        if not symbol:
            raise NotSupported(self.id + ': fetchOrders requires a `symbol` parameter.')
        await self.load_markets()
        market = self.market(symbol)
        request = self.prepare_history_request(market, since, limit)
        response = await self.privatePostOrderHistory(self.extend(request, params))
        return self.parse_orders(response['orders'], market)

    async def fetch_open_orders(self, symbol=None, since=None, limit=None, params={}):
        if not symbol:
            raise NotSupported(self.id + ': fetchOpenOrders requires a `symbol` parameter.')
        await self.load_markets()
        market = self.market(symbol)
        request = self.prepare_history_request(market, since, limit)
        response = await self.privatePostOrderOpen(self.extend(request, params))
        return self.parse_orders(response['orders'], market)

    async def fetch_closed_orders(self, symbol=None, since=None, limit=None, params={}):
        orders = await self.fetch_orders(symbol, since, limit, params)
        return self.filter_by(orders, 'status', 'closed')
        return []

    async def fetch_my_trades(self, symbol=None, since=None, limit=None, params={}):
        if not symbol:
            raise NotSupported(self.id + ': fetchMyTrades requires a `symbol` parameter.')
        await self.load_markets()
        market = self.market(symbol)
        request = self.prepare_history_request(market, since, limit)
        response = await self.privatePostOrderTradeHistory(self.extend(request, params))
        return self.parse_my_trades(response['trades'], market)

    def nonce(self):
        return self.milliseconds()

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        uri = '/' + self.implode_params(path, params)
        url = self.urls['api'] + uri
        if api == 'public':
            if params:
                url += '?' + self.urlencode(params)
        else:
            self.check_required_credentials()
            nonce = str(self.nonce())
            auth = uri + "\n" + nonce + "\n"
            headers = {
                'Content-Type': 'application/json',
                'apikey': self.apiKey,
                'timestamp': nonce,
            }
            if method == 'POST':
                body = self.json(params)
                auth += body
            secret = base64.b64decode(self.secret)
            signature = self.hmac(self.encode(auth), secret, hashlib.sha512, 'base64')
            headers['signature'] = self.decode(signature)
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    async def request(self, path, api='public', method='GET', params={}, headers=None, body=None):
        response = await self.fetch2(path, api, method, params, headers, body)
        if api == 'private':
            if 'success' in response:
                if not response['success']:
                    raise ExchangeError(self.id + ' ' + self.json(response))
            return response
        return response
