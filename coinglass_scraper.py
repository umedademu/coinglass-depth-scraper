#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coinglass.com BTC-USDT Order Book Scraper Final Version
実際のページ構造に基づいた正確な板情報取得
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from collections import deque
import matplotlib.dates as mdates
import traceback
import os
import sys
import platform
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3
import pystray
from PIL import Image
from cloud_sync import CloudSyncManager


class CoinglassScraper:
    def __init__(self):
        self.driver = None
        self.is_running = False
        self.update_interval = 60  # 固定60秒間隔
        self.url = "https://www.coinglass.com/ja/mergev2/BTC-USDT"
        self.last_valid_price = None  # 前回の有効な価格を保存
        
        # ログ設定
        # AppDataフォルダにログを保存
        appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
        os.makedirs(appdata_dir, exist_ok=True)
        log_file = os.path.join(appdata_dir, 'coinglass_scraper.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_driver(self, headless=False):
        """Seleniumドライバーのセットアップ"""
        try:
            options = Options()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # User-Agentの設定
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # ChromeDriverの設定
            try:
                if platform.system() == "Windows":
                    driver_path = ChromeDriverManager(version="latest", cache_valid_range=1).install()
                    
                    # 正しいexeパスを探す
                    if os.path.exists(driver_path):
                        if os.path.isdir(driver_path):
                            exe_path = os.path.join(driver_path, "chromedriver.exe")
                            if not os.path.exists(exe_path):
                                for root, dirs, files in os.walk(driver_path):
                                    if "chromedriver.exe" in files:
                                        exe_path = os.path.join(root, "chromedriver.exe")
                                        break
                            driver_path = exe_path
                        
                        self.logger.info(f"ChromeDriver path: {driver_path}")
                        service = Service(driver_path)
                else:
                    service = Service(ChromeDriverManager().install())
                
                self.driver = webdriver.Chrome(service=service, options=options)
                
            except Exception as e:
                self.logger.error(f"ChromeDriverManagerでエラー: {str(e)}")
                self.logger.info("システムのPATHからchromedriverを探します...")
                self.driver = webdriver.Chrome(options=options)
            
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            self.logger.info("Chromeドライバーを初期化しました")
            return True
            
        except Exception as e:
            self.logger.error(f"ドライバーの初期化に失敗しました: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def initialize_page(self, headless=False):
        """初回のみ実行：ページを開いてグルーピングを設定"""
        try:
            if not self.driver:
                if not self.setup_driver(headless=headless):
                    return False
            
            # ページを読み込み
            self.driver.get(self.url)
            self.logger.info(f"ページにアクセス: {self.url}")
            
            # ページの基本的な読み込みを待つ
            WebDriverWait(self.driver, 30).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # グルーピングを100に設定（オーダーブック表示前）
            self.set_grouping_to_100()
            
            # オーダーブックの読み込みを待機
            if not self.wait_for_order_book():
                return False
            
            self.logger.info("初期化が完了しました")
            return True
            
        except Exception as e:
            self.logger.error(f"ページ初期化エラー: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def wait_for_order_book(self):
        """オーダーブックの読み込みを待機"""
        try:
            # オーダーブックの要素が表示されるまで待つ
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "obv2-item"))
            )
            
            # データが安定するまで少し待つ
            time.sleep(2)
            
            return True
        except TimeoutException:
            self.logger.error("オーダーブックの読み込みがタイムアウトしました")
            return False

    def set_grouping_to_100(self):
        """グルーピングを100に設定"""
        try:
            self.logger.info("グルーピングを100に設定中...")
            
            # 複数のMuiSelectボタンから正しいものを探す
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.MuiSelect-button")
            dropdown_button = None
            
            for button in buttons:
                button_text = button.text.strip()
                self.logger.debug(f"ボタン発見: '{button_text}', 表示: {button.is_displayed()}")
                if button_text in ['10', '50', '100'] and button.is_displayed():
                    dropdown_button = button
                    break
            
            if not dropdown_button:
                # より具体的なXPathで再試行
                dropdown_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'MuiSelect-button') and (text()='10' or text()='50' or text()='100')]"))
                )
            
            # 現在の値を確認
            current_value = dropdown_button.text.strip()
            self.logger.info(f"現在のグルーピング値: {current_value}")
            
            if current_value == "100":
                self.logger.info("グルーピングは既に100に設定されています")
                return True
            
            # プルダウンをクリック
            self.logger.debug("プルダウンメニューをクリックします")
            dropdown_button.click()
            
            # メニューが開くのを待つ
            time.sleep(1)
            
            # 100のオプションを複数の方法で探す
            option_100 = None
            
            # 方法1: role属性を使用
            try:
                option_100 = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//li[@role='option' and text()='100']"))
                )
                self.logger.debug("role='option'で100を発見")
            except:
                pass
            
            # 方法2: MUIのポップアップ内を探す
            if not option_100:
                try:
                    option_100 = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, "//ul[contains(@class, 'MuiSelect-listbox')]//li[text()='100']"))
                    )
                    self.logger.debug("MuiSelect-listboxで100を発見")
                except:
                    pass
            
            # 方法3: 単純にli要素を探す
            if not option_100:
                try:
                    option_100 = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, "//li[text()='100']"))
                    )
                    self.logger.debug("単純なli要素で100を発見")
                except:
                    pass
            
            if option_100:
                option_100.click()
                self.logger.info("100をクリックしました")
                
                # 設定が反映されるのを待つ
                time.sleep(1)
                
                # 確認のため再度ボタンのテキストを取得
                new_value = dropdown_button.text.strip()
                if new_value == "100":
                    self.logger.info("グルーピングを100に設定しました")
                    return True
                else:
                    self.logger.warning(f"設定後の値が期待と異なります: {new_value}")
                    return False
            else:
                self.logger.warning("100のオプションが見つかりませんでした")
                # エスケープキーでメニューを閉じる
                from selenium.webdriver.common.keys import Keys
                dropdown_button.send_keys(Keys.ESCAPE)
                return False
            
        except TimeoutException as e:
            self.logger.warning(f"グルーピング設定のタイムアウト: {str(e)} - デフォルト値で続行します")
            return False
        except Exception as e:
            self.logger.warning(f"グルーピング設定エラー: {str(e)} - デフォルト値で続行します")
            self.logger.debug(f"エラーの詳細: {traceback.format_exc()}")
            return False

    def get_full_order_book_totals(self):
        """スクロールして売り板と買い板の最端のトータル値を取得"""
        try:
            self.logger.info("完全な板情報を取得中...")
            
            # orderbookクラスの要素を取得（0:売り板、1:買い板）
            orderbooks = self.driver.find_elements(By.CLASS_NAME, "orderbook")
            
            if len(orderbooks) < 2:
                self.logger.warning("orderbook要素が見つかりません")
                return None, None
            
            # 売り板を最上部までスクロール
            self.logger.debug("売り板を最上部までスクロール中...")
            self.driver.execute_script("arguments[0].scrollTop = 0", orderbooks[0])
            time.sleep(1)  # データ表示を待つ
            
            # 売り板の最上部のトータル値を取得
            ask_total = self.driver.execute_script("""
                const orderbook = arguments[0];
                const totalElements = orderbook.querySelectorAll('.obv2-item-total');
                
                if (totalElements.length > 0) {
                    // 最初の要素の最初の子要素（div）のテキストのみを取得
                    const totalDiv = totalElements[0].querySelector('div');
                    if (totalDiv) {
                        const totalText = totalDiv.textContent;
                        return parseFloat(totalText.replace(/,/g, ''));
                    }
                }
                return null;
            """, orderbooks[0])
            
            self.logger.info(f"売り板の完全なトータル: {ask_total}")
            
            # 買い板を最下部までスクロール
            self.logger.debug("買い板を最下部までスクロール中...")
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", orderbooks[1])
            time.sleep(1)  # データ表示を待つ
            
            # 買い板の最下部のトータル値を取得
            bid_total = self.driver.execute_script("""
                const orderbook = arguments[0];
                const totalElements = orderbook.querySelectorAll('.obv2-item-total');
                
                if (totalElements.length > 0) {
                    // 最後の要素の最初の子要素（div）のテキストのみを取得
                    const lastIndex = totalElements.length - 1;
                    const totalDiv = totalElements[lastIndex].querySelector('div');
                    if (totalDiv) {
                        const totalText = totalDiv.textContent;
                        return parseFloat(totalText.replace(/,/g, ''));
                    }
                }
                return null;
            """, orderbooks[1])
            
            self.logger.info(f"買い板の完全なトータル: {bid_total}")
            
            # スクロールを元の位置（中央付近）に戻す
            self.logger.debug("スクロール位置を復元中...")
            self.driver.execute_script("""
                // 売り板を中央付近に
                arguments[0].scrollTop = arguments[0].scrollHeight / 2;
                // 買い板を上部付近に
                arguments[1].scrollTop = 0;
            """, orderbooks[0], orderbooks[1])
            
            return ask_total, bid_total
            
        except Exception as e:
            self.logger.error(f"完全な板情報の取得エラー: {str(e)}")
            self.logger.debug(f"エラーの詳細: {traceback.format_exc()}")
            return None, None

    def _fetch_price_from_page(self):
        """ページから価格を取得する内部メソッド"""
        try:
            # 方法1: 画面下部のバーから正確な価格を取得
            # 複数の取引所の価格が表示されているエリアから取得
            price_data = self.driver.execute_script("""
                // Numberクラスを持つ要素を探す（画面下部のバー）
                const numberElements = document.querySelectorAll('div.Number');
                
                for (const elem of numberElements) {
                    const text = elem.textContent.trim();
                    // 小数点を含む価格形式かチェック
                    if (text && text.includes('.') && text.length > 5) {
                        const value = parseFloat(text.replace(/,/g, ''));
                        // BTCの妥当な価格範囲内かチェック
                        if (!isNaN(value) && value > 50000 && value < 200000) {
                            // Y座標が画面下部（700より大きい）かチェック
                            const rect = elem.getBoundingClientRect();
                            if (rect.top > 700) {
                                return value;
                            }
                        }
                    }
                }
                
                // 方法2: XPathで特定の位置から取得（フォールバック）
                try {
                    // 最初の価格要素（通常Binance）
                    const xpath = '//*[@id="__next"]/div[2]/div[2]/div[2]/div[1]/div[2]/div[1]/div[4]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]';
                    const elem = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (elem) {
                        const text = elem.textContent.trim();
                        if (text && text.includes('.')) {
                            return parseFloat(text.replace(/,/g, ''));
                        }
                    }
                } catch (e) {
                    console.error('XPath取得エラー:', e);
                }
                
                return null;
            """)
            
            if price_data:
                self.logger.info(f"正確な現在価格を取得: {price_data}")
                return price_data
            
            # 方法2: 板情報の中央値から推測（フォールバック）
            self.logger.warning("正確な価格が取得できません。板情報から推測します")
            current_price = self.driver.execute_script("""
                const priceElements = document.querySelectorAll('.obv2-item-price');
                if (priceElements.length > 0) {
                    const midIndex = Math.floor(priceElements.length / 2);
                    return parseFloat(priceElements[midIndex].textContent.replace(/,/g, ''));
                }
                return null;
            """)
            
            if current_price:
                self.logger.info(f"板情報から推測した価格: {current_price}")
                return current_price
            
            # 価格が取得できない場合はNoneを返す
            return None
            
        except Exception as e:
            self.logger.error(f"価格取得エラー: {str(e)}")
            return None
    
    def get_current_price(self):
        """現在価格を取得（再試行機能付き）"""
        # 1回目の試行
        price = self._fetch_price_from_page()
        if price and price > 0:
            self.last_valid_price = price
            return price
        
        # 1回目が失敗したら、少し待って再試行
        self.logger.warning("価格取得に失敗。再試行します...")
        time.sleep(0.5)
        
        # 2回目の試行
        price = self._fetch_price_from_page()
        if price and price > 0:
            self.last_valid_price = price
            return price
        
        # 両方失敗した場合、前回の有効な価格を使用
        if self.last_valid_price:
            self.logger.warning(f"価格取得に失敗。前回の価格 {self.last_valid_price} を使用します")
            return self.last_valid_price
        else:
            # 初回起動時など、前回値もない場合はエラー
            self.logger.error("価格を取得できません。前回の値もありません")
            raise ValueError("現在価格を取得できません")

    def get_order_book_data(self):
        """売り板と買い板の総量を取得（実際の構造に基づく）"""
        try:
            if not self.driver:
                self.logger.error("ドライバーが初期化されていません")
                return None
            
            # 現在価格を取得
            try:
                current_price = self.get_current_price()
                self.logger.info(f"現在価格: {current_price}")
            except ValueError as e:
                self.logger.error(f"価格取得エラー: {str(e)}")
                return None
            
            # 完全な板情報（スクロールして最端のトータル値）を取得
            full_ask_total, full_bid_total = self.get_full_order_book_totals()
            
            # JavaScriptで板情報を取得（表示範囲のみ - 従来の処理）
            order_book_data = self.driver.execute_script("""
                function getOrderBookData(currentPrice) {
                    let askTotal = 0;  // 売り板総量
                    let bidTotal = 0;  // 買い板総量
                    
                    // すべての板情報要素を取得
                    const orderItems = document.querySelectorAll('.obv2-item');
                    
                    orderItems.forEach(item => {
                        try {
                            // 価格を取得
                            const priceElem = item.querySelector('.obv2-item-price');
                            if (!priceElem) return;
                            
                            const price = parseFloat(priceElem.textContent.replace(/,/g, ''));
                            if (isNaN(price)) return;
                            
                            // 数量を取得
                            const amountElem = item.querySelector('.obv2-item-amount');
                            if (!amountElem) return;
                            
                            const amount = parseFloat(amountElem.textContent.replace(/,/g, ''));
                            if (isNaN(amount)) return;
                            
                            // 現在価格と比較して売り板か買い板か判定
                            if (price > currentPrice) {
                                // 売り板（Ask）
                                askTotal += amount;
                            } else if (price < currentPrice) {
                                // 買い板（Bid）
                                bidTotal += amount;
                            }
                            
                            // クラス名でも判定（バックアップ）
                            if (item.classList.contains('asks')) {
                                if (price <= currentPrice) {
                                    // 誤分類を修正
                                    bidTotal += amount;
                                    askTotal -= amount;
                                }
                            }
                        } catch (e) {
                            console.error('Error processing order item:', e);
                        }
                    });
                    
                    // デバッグ情報も含める
                    return {
                        askTotal: askTotal,
                        bidTotal: bidTotal,
                        currentPrice: currentPrice,
                        totalItems: orderItems.length,
                        timestamp: new Date().toISOString()
                    };
                }
                
                return getOrderBookData(arguments[0]);
            """, current_price)
            
            
            # 完全な板情報をorder_book_dataに追加
            if full_ask_total is not None and full_bid_total is not None:
                order_book_data['fullAskTotal'] = full_ask_total
                order_book_data['fullBidTotal'] = full_bid_total
                self.logger.info(f"完全な板情報: 売り板総量={full_ask_total:.2f}, 買い板総量={full_bid_total:.2f}")
            else:
                # スクロール取得に失敗した場合は従来の値を使用
                order_book_data['fullAskTotal'] = order_book_data['askTotal']
                order_book_data['fullBidTotal'] = order_book_data['bidTotal']
            
            self.logger.info(f"表示範囲のデータ: 売り板総量={order_book_data['askTotal']:.2f}, "
                           f"買い板総量={order_book_data['bidTotal']:.2f}")
            
            return order_book_data
            
        except Exception as e:
            self.logger.error(f"データ取得エラー: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None


    def close_driver(self):
        """ドライバーを閉じる"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("ドライバーを終了しました")
            except:
                pass
            self.driver = None


class ScraperGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Coinglass BTC-USDT Order Book Monitor v1.18")
        self.root.geometry("1200x900")  # ウィンドウサイズを拡大
        
        # ウィンドウアイコンを設定
        if os.path.exists('icon.ico'):
            try:
                self.root.iconbitmap('icon.ico')
            except Exception as e:
                # アイコン設定に失敗した場合は無視
                pass
        
        self.scraper = CoinglassScraper()
        self.scraper_thread = None
        
        # グラフ用のデータ履歴（全データ保持）
        self.time_history = []
        self.ask_history = []
        self.bid_history = []
        
        # 初期値を設定
        self.cloud_sync = None
        
        self.setup_ui()
        self.setup_graph()
        
        # UIセットアップ後にクラウド同期を初期化
        try:
            self.cloud_sync = CloudSyncManager(log_callback=self.add_log)
            if self.cloud_sync.enabled:
                self.add_log("クラウド同期機能が有効です", "INFO")
        except Exception as e:
            self.add_log(f"クラウド同期の初期化に失敗: {str(e)}", "WARNING")
            self.cloud_sync = None
        
        # データベースの初期化
        self.init_database()
        # 既存データの読み込み
        self.load_historical_data()
        
        # システムトレイ関連
        self.tray_icon = None
        self.is_minimized_to_tray = False
        
    def setup_ui(self):
        """UIのセットアップ"""
        # スタイル設定
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Value.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Small.TLabel', font=('Arial', 9))
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 1行目: タイトルと板情報を横一列に配置
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # タイトル
        ttk.Label(top_frame, text="BTC-USDT", style='Title.TLabel').grid(row=0, column=0, padx=10)
        
        # 現在価格
        price_frame = ttk.Frame(top_frame)
        price_frame.grid(row=0, column=1, padx=10)
        ttk.Label(price_frame, text="価格:", font=('Arial', 10)).pack(side=tk.LEFT)
        self.price_label = ttk.Label(price_frame, text="---", font=('Arial', 11, 'bold'))
        self.price_label.pack(side=tk.LEFT, padx=5)
        
        # 売り板総量
        ask_frame = ttk.Frame(top_frame)
        ask_frame.grid(row=0, column=2, padx=10)
        ttk.Label(ask_frame, text="売板:", font=('Arial', 10)).pack(side=tk.LEFT)
        self.ask_label = ttk.Label(ask_frame, text="---", font=('Arial', 11, 'bold'), foreground='red')
        self.ask_label.pack(side=tk.LEFT, padx=5)
        
        # 買い板総量
        bid_frame = ttk.Frame(top_frame)
        bid_frame.grid(row=0, column=3, padx=10)
        ttk.Label(bid_frame, text="買板:", font=('Arial', 10)).pack(side=tk.LEFT)
        self.bid_label = ttk.Label(bid_frame, text="---", font=('Arial', 11, 'bold'), foreground='green')
        self.bid_label.pack(side=tk.LEFT, padx=5)
        
        # 比率
        ratio_frame = ttk.Frame(top_frame)
        ratio_frame.grid(row=0, column=4, padx=10)
        ttk.Label(ratio_frame, text="比率:", font=('Arial', 10)).pack(side=tk.LEFT)
        self.ratio_label = ttk.Label(ratio_frame, text="---", font=('Arial', 11, 'bold'))
        self.ratio_label.pack(side=tk.LEFT, padx=5)
        
        # 差枚
        diff_frame = ttk.Frame(top_frame)
        diff_frame.grid(row=0, column=5, padx=10)
        ttk.Label(diff_frame, text="差枚:", font=('Arial', 10)).pack(side=tk.LEFT)
        self.diff_label = ttk.Label(diff_frame, text="---", font=('Arial', 11, 'bold'))
        self.diff_label.pack(side=tk.LEFT, padx=5)
        
        # 最終更新時刻
        self.time_label = ttk.Label(top_frame, text="---", font=('Arial', 9))
        self.time_label.grid(row=0, column=6, padx=10)
        
        # 2行目: コントロールボタンと設定を横一列に配置
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.start_button = ttk.Button(control_frame, text="開始", command=self.start_scraping,
                                      width=10)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="停止", command=self.stop_scraping, 
                                     state='disabled', width=10)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        self.clear_button = ttk.Button(control_frame, text="クリア", 
                                      command=self.clear_all, width=10)
        self.clear_button.grid(row=0, column=2, padx=5)
        
        # 区切り線
        ttk.Separator(control_frame, orient='vertical').grid(row=0, column=3, sticky='ns', padx=10)
        
        # 時間足選択
        ttk.Label(control_frame, text="時間足:", font=('Arial', 10)).grid(row=0, column=4, padx=5)
        self.timeframe_var = tk.StringVar(value="1分")
        self.all_timeframes = ["1分", "3分", "5分", "15分", "30分", "1時間", "2時間", "4時間", "1日"]
        self.timeframe_combo = ttk.Combobox(control_frame, textvariable=self.timeframe_var, 
                                     values=["1分"], width=8, state="readonly")  # 初期は1分のみ
        self.timeframe_combo.grid(row=0, column=5, padx=5)
        self.timeframe_combo.bind('<<ComboboxSelected>>', lambda e: self.update_graph())
        
        # ヘッドレスモード
        self.headless_var = tk.BooleanVar(value=True)
        headless_check = ttk.Checkbutton(control_frame, text="ヘッドレスモード", 
                                        variable=self.headless_var)
        headless_check.grid(row=0, column=6, padx=10)
        
        # クラウド同期状態
        if hasattr(self, 'cloud_sync') and self.cloud_sync and self.cloud_sync.enabled:
            ttk.Separator(control_frame, orient='vertical').grid(row=0, column=7, sticky='ns', padx=10)
            self.sync_status_label = ttk.Label(control_frame, text="☁ 同期: 待機中", 
                                             font=('Arial', 9), foreground='green')
            self.sync_status_label.grid(row=0, column=8, padx=5)
            # 定期的に同期状態を更新
            self.update_sync_status()
        
        # PanedWindowを作成（縦分割、サイズ調整可能）
        paned_window = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned_window.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # グラフ表示エリア（拡大）
        self.graph_frame = ttk.LabelFrame(padding="5")
        self.graph_frame.configure(text="板推移グラフ")
        
        # ログ表示エリア
        log_frame = ttk.LabelFrame(padding="5")
        log_frame.configure(text="ログ")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=110)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # PanedWindowにグラフとログを追加
        paned_window.add(self.graph_frame, weight=3)  # グラフは重み3
        paned_window.add(log_frame, weight=1)  # ログは重み1
        
        # グリッドの重み設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)  # PanedWindowに重みを設定
        self.graph_frame.columnconfigure(0, weight=1)
        self.graph_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def update_display(self, data):
        """表示を更新"""
        if data and data.get('askTotal', 0) > 0 or data.get('bidTotal', 0) > 0:
            ask_total = data.get('askTotal', 0)
            bid_total = data.get('bidTotal', 0)
            current_price = data.get('currentPrice', 0)
            
            # 現在価格（小数点第1位まで表示）
            if current_price > 0:
                self.price_label.config(text=f"{current_price:,.1f}")
            
            # 売り板・買い板（完全な板情報を優先表示）
            full_ask_total = data.get('fullAskTotal', ask_total)
            full_bid_total = data.get('fullBidTotal', bid_total)
            
            self.ask_label.config(text=f"{full_ask_total:,.1f}")
            self.bid_label.config(text=f"{full_bid_total:,.1f}")
            
            # 比率と差額を計算（完全な板情報を使用）
            if full_ask_total > 0:
                ratio = full_bid_total / full_ask_total
                self.ratio_label.config(text=f"{ratio:.3f}")
                if ratio > 1:
                    self.ratio_label.config(foreground='green')
                else:
                    self.ratio_label.config(foreground='red')
            
            diff = full_bid_total - full_ask_total
            self.diff_label.config(text=f"{diff:+,.2f}")
            if diff > 0:
                self.diff_label.config(foreground='green')
            else:
                self.diff_label.config(foreground='red')
            
            self.time_label.config(text=f"{datetime.now().strftime('%H:%M:%S')}")
            
            log_message = (f"更新成功: 売り板={full_ask_total:,.2f}, "
                          f"買い板={full_bid_total:,.2f}, "
                          f"現在価格={current_price:,.0f}")
            self.add_log(log_message)
            
            
            # グラフ用データを追加
            now = datetime.now()
            self.time_history.append(now)
            self.ask_history.append(full_ask_total)
            self.bid_history.append(full_bid_total)
            
            # データベースに保存
            self.save_to_database(now, full_ask_total, full_bid_total, current_price)
            
            # 選択可能な時間足を更新
            self.update_timeframe_options()
            
            # グラフを更新
            self.update_graph()
            
            # 前回値を更新
            self.last_ask_total = full_ask_total
            self.last_bid_total = full_bid_total
        else:
            self.add_log("データ取得に失敗しました（板情報が空です）", "WARNING")
    
    def add_log(self, message, level="INFO"):
        """ログを追加"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def update_timeframe_options(self):
        """データ量に基づいて選択可能な時間足を更新"""
        data_count = len(self.time_history)
        
        # 各時間足に必要な最小データ数（少なくとも2点は必要）
        min_data_required = {
            "1分": 2,
            "3分": 3,
            "5分": 5,
            "15分": 15,
            "30分": 30,
            "1時間": 60,
            "2時間": 120,
            "4時間": 240,
            "1日": 1440
        }
        
        # 選択可能な時間足をフィルタリング
        available_timeframes = []
        for tf in self.all_timeframes:
            if data_count >= min_data_required[tf]:
                available_timeframes.append(tf)
        
        # コンボボックスの値を更新
        current_selection = self.timeframe_var.get()
        self.timeframe_combo['values'] = available_timeframes
        
        # 現在の選択が無効になった場合、最大の有効な時間足を選択
        if current_selection not in available_timeframes and available_timeframes:
            self.timeframe_var.set(available_timeframes[-1])
            self.update_graph()
    
    def setup_graph(self):
        """グラフをセットアップ"""
        # matplotlibのスタイル設定
        plt.style.use('dark_background')
        
        # フィギュアとサブプロットを作成
        self.fig = Figure(figsize=(10, 5), dpi=80)
        self.fig.patch.set_facecolor('#2b2b2b')
        
        # 売り板用のサブプロット（上側）
        self.ax_ask = self.fig.add_subplot(2, 1, 1)
        self.ax_ask.set_facecolor('#1e1e1e')
        self.ax_ask.grid(True, alpha=0.2, color='#444444')
        self.ax_ask.set_ylim(0, 1)  # 初期値、自動調整される
        
        # 買い板用のサブプロット（下側）
        self.ax_bid = self.fig.add_subplot(2, 1, 2)
        self.ax_bid.set_facecolor('#1e1e1e')
        self.ax_bid.grid(True, alpha=0.2, color='#444444')
        self.ax_bid.set_ylim(0, 1)  # 初期値、自動調整される
        
        # 売り板のY軸を反転（下向きに表示）
        self.ax_ask.invert_yaxis()
        
        # レイアウト調整
        self.fig.tight_layout(pad=2.0)
        
        # tkinterにキャンバスを埋め込む
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # TradingView風のマウス操作を実装
        self.setup_interactive_controls()
        
        # 初期グラフを描画
        self.canvas.draw()
        
        # 前回値を保持（最適値選定用）
        self.last_ask_total = None
        self.last_bid_total = None
    
    def setup_interactive_controls(self):
        """TradingView風のマウス操作を設定"""
        # ドラッグ用の変数
        self.press = None
        self.cur_xlim_ask = None
        self.cur_ylim_ask = None
        self.cur_xlim_bid = None
        self.cur_ylim_bid = None
        
        # マウスホイールでズーム
        def on_scroll(event):
            try:
                # どちらのグラフ上でも両方のグラフをズーム（X軸のみ）
                # 現在の表示範囲を取得
                xlim_ask = self.ax_ask.get_xlim()
                
                # マウス位置を取得（グラフ内の座標）
                xdata = event.xdata
                
                # グラフ外でホイールを回した場合は中心でズーム
                if xdata is None:
                    xdata = (xlim_ask[0] + xlim_ask[1]) / 2
                
                # ズーム率（ホイール上=拡大、下=縮小）
                if event.button == 'up':
                    scale = 0.9  # 10%拡大
                elif event.button == 'down':
                    scale = 1.1  # 10%縮小
                else:
                    return
                
                # X軸のズーム（両グラフ共通）
                new_xlim = [xdata - (xdata - xlim_ask[0]) * scale,
                           xdata + (xlim_ask[1] - xdata) * scale]
                
                # X軸を両グラフに設定
                self.ax_ask.set_xlim(new_xlim)
                self.ax_bid.set_xlim(new_xlim)
                
                # グラフを再描画
                self.canvas.draw_idle()
            except Exception as e:
                self.logger.error(f"ズームエラー: {e}")
        
        # マウスボタンを押したとき
        def on_press(event):
            # 左クリックのみ処理
            if event.button != 1:
                return
            
            self.press = (event.xdata, event.ydata)
            self.cur_xlim_ask = self.ax_ask.get_xlim()
            self.cur_ylim_ask = self.ax_ask.get_ylim()
            self.cur_xlim_bid = self.ax_bid.get_xlim()
            self.cur_ylim_bid = self.ax_bid.get_ylim()
        
        # マウスを動かしたとき（ドラッグ）
        def on_motion(event):
            # ドラッグ中でない場合は何もしない
            if self.press is None:
                return
            if event.xdata is None:
                return
                
            # X軸の移動量を計算
            dx = self.press[0] - event.xdata if self.press[0] is not None else 0
            
            # X軸の移動（両グラフ共通）
            self.ax_ask.set_xlim(self.cur_xlim_ask[0] + dx, self.cur_xlim_ask[1] + dx)
            self.ax_bid.set_xlim(self.cur_xlim_bid[0] + dx, self.cur_xlim_bid[1] + dx)
            
            # グラフを再描画
            self.canvas.draw_idle()
        
        # マウスボタンを離したとき
        def on_release(event):
            self.press = None
        
        # ダブルクリックでリセット
        def on_double_click(event):
            if event.dblclick:
                # 両グラフを元の表示に戻す
                self.ax_ask.autoscale()
                self.ax_bid.autoscale()
                self.canvas.draw_idle()
        
        # イベントをキャンバスに接続
        self.canvas.mpl_connect('scroll_event', on_scroll)
        self.canvas.mpl_connect('button_press_event', on_press)
        self.canvas.mpl_connect('button_press_event', on_double_click)
        self.canvas.mpl_connect('motion_notify_event', on_motion)
        self.canvas.mpl_connect('button_release_event', on_release)
    
    def select_best_values(self, data_list):
        """3つの取得データから最適値を選定（最大値を採用）"""
        if not data_list or len(data_list) == 0:
            return None
            
        # すべてNoneの場合
        valid_data = [d for d in data_list if d is not None]
        if not valid_data:
            return None
            
        # 各データのfullAskTotalとfullBidTotalの合計を計算し、最大のものを選定
        best_data = None
        max_total = -1
        
        for data in valid_data:
            if 'fullAskTotal' not in data or 'fullBidTotal' not in data:
                continue
                
            # 売り板と買い板の合計値
            total = data['fullAskTotal'] + data['fullBidTotal']
            
            if total > max_total:
                max_total = total
                best_data = data
        
        # 最大値のデータが見つかった場合はログ出力
        if best_data:
            self.add_log(f"3回の取得から最大値を選定: 売り板={best_data['fullAskTotal']:.2f}, 買い板={best_data['fullBidTotal']:.2f}")
        
        return best_data
    
    def init_database(self):
        """SQLiteデータベースを初期化"""
        try:
            # AppDataフォルダにデータベースを保存
            appdata_dir = os.path.join(os.environ.get('APPDATA', ''), 'CoinglassScraper')
            os.makedirs(appdata_dir, exist_ok=True)
            self.db_path = os.path.join(appdata_dir, "btc_usdt_order_book.db")
            # スレッドセーフな接続を作成
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self.conn.cursor()
            
            # テーブルの作成
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_book_history (
                    timestamp TEXT PRIMARY KEY,
                    ask_total REAL NOT NULL,
                    bid_total REAL NOT NULL,
                    price REAL NOT NULL
                )
            """)
            
            # インデックスの作成（高速化のため）
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON order_book_history(timestamp)
            """)
            
            self.conn.commit()
            self.add_log("データベースを初期化しました")
            
        except Exception as e:
            self.add_log(f"データベース初期化エラー: {str(e)}", "ERROR")
            
    def save_to_database(self, timestamp, ask_total, bid_total, price):
        """データをデータベースに保存"""
        try:
            # タイムスタンプを分単位に丸める（秒を00にする）
            rounded_timestamp = timestamp.replace(second=0, microsecond=0)
            
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO order_book_history 
                (timestamp, ask_total, bid_total, price)
                VALUES (?, ?, ?, ?)
            """, (rounded_timestamp.isoformat(), ask_total, bid_total, price))
            
            self.conn.commit()
            
            # クラウド同期を実行（丸めたタイムスタンプを使用）
            if hasattr(self, 'cloud_sync') and self.cloud_sync:
                self.cloud_sync.sync_data_async(
                    rounded_timestamp.isoformat(),
                    ask_total,
                    bid_total,
                    price
                )
                
                # 第5段階の実装：リアルタイム欠損補完を削除
                # 以下のコードをコメントアウト（異なる粒度のデータ混在を防ぐ）
                # if rounded_timestamp.minute % 5 == 0:
                #     import threading
                #     check_thread = threading.Thread(
                #         target=self.check_and_fetch_missing_data_async,
                #         daemon=True
                #     )
                #     check_thread.start()
            
            # 300日以上前のデータを削除
            cutoff_date = (datetime.now() - timedelta(days=300)).isoformat()
            cursor.execute("""
                DELETE FROM order_book_history 
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            self.conn.commit()
            
        except Exception as e:
            self.add_log(f"データ保存エラー: {str(e)}", "ERROR")
            # 3回までリトライ
            for i in range(3):
                try:
                    time.sleep(0.1)
                    self.conn.commit()
                    break
                except:
                    if i == 2:
                        self.add_log("データ保存に失敗しました", "ERROR")
                        
    def update_sync_status(self):
        """同期状態を更新"""
        if hasattr(self, 'sync_status_label') and self.cloud_sync:
            status = self.cloud_sync.get_sync_status()
            if status['last_sync']:
                self.sync_status_label.config(text="☁ 同期: 完了", foreground='green')
            else:
                self.sync_status_label.config(text="☁ 同期: 待機中", foreground='gray')
            
            # 5秒後に再度更新
            self.root.after(5000, self.update_sync_status)
    
    def check_and_fetch_missing_data_async(self):
        """非同期で欠損データをチェックして取得（リアルタイム欠損補完は無効化）"""
        # 第5段階の実装：リアルタイム欠損補完を削除
        # 異なる粒度のデータ混在を防ぐため、6分以上の欠損補完機能を無効化
        return
    
    def fetch_initial_timeframe_data(self):
        """各時間足テーブルから初期データを取得してローカルDBに保存"""
        try:
            # cloud_syncのfetch_initial_dataメソッドを持っている
            all_timeframe_data = self.cloud_sync.fetch_initial_data()
            
            if not all_timeframe_data:
                self.add_log("時間足データの取得に失敗しました", "WARNING")
                return
            
            cursor = self.conn.cursor()
            total_inserted = 0
            
            # 各時間足のデータをローカルDBに保存
            for table_name, records in all_timeframe_data.items():
                if not records:
                    continue
                    
                table_inserted = 0
                for record in records:
                    try:
                        # タイムスタンプからタイムゾーン情報を除去
                        timestamp_str = record['timestamp']
                        if '+' in timestamp_str or 'T' in timestamp_str:
                            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            timestamp_str = dt.replace(tzinfo=None).isoformat()
                        
                        # 既存データをチェック
                        cursor.execute("""
                            SELECT ask_total, bid_total FROM order_book_history
                            WHERE timestamp = ?
                        """, (timestamp_str,))
                        
                        existing = cursor.fetchone()
                        
                        if existing:
                            # 最大値を選択して更新
                            if record['ask_total'] > existing[0] or record['bid_total'] > existing[1]:
                                cursor.execute("""
                                    UPDATE order_book_history 
                                    SET ask_total = ?, bid_total = ?, price = ?
                                    WHERE timestamp = ?
                                """, (
                                    max(record['ask_total'], existing[0]),
                                    max(record['bid_total'], existing[1]),
                                    record['price'],
                                    timestamp_str
                                ))
                                if cursor.rowcount > 0:
                                    table_inserted += 1
                        else:
                            # 新規挿入
                            cursor.execute("""
                                INSERT INTO order_book_history 
                                (timestamp, ask_total, bid_total, price)
                                VALUES (?, ?, ?, ?)
                            """, (
                                timestamp_str,
                                record['ask_total'],
                                record['bid_total'],
                                record['price']
                            ))
                            if cursor.rowcount > 0:
                                table_inserted += 1
                                
                                # メモリ上の履歴にも追加
                                timestamp = datetime.fromisoformat(timestamp_str)
                                self.time_history.append(timestamp)
                                self.ask_history.append(record['ask_total'])
                                self.bid_history.append(record['bid_total'])
                                
                    except Exception as e:
                        # 個別のレコードエラーは継続
                        continue
                
                if table_inserted > 0:
                    # テーブル名から時間足名を取得
                    timeframe_names = {
                        'order_book_shared': '5分足',
                        'order_book_15min': '15分足',
                        'order_book_30min': '30分足',
                        'order_book_1hour': '1時間足',
                        'order_book_2hour': '2時間足',
                        'order_book_4hour': '4時間足',
                        'order_book_daily': '日足'
                    }
                    timeframe_name = timeframe_names.get(table_name, table_name)
                    self.add_log(f"{timeframe_name}: {table_inserted}件のデータをローカルDBに保存")
                    total_inserted += table_inserted
            
            if total_inserted > 0:
                self.conn.commit()
                self.add_log(f"合計{total_inserted}件の時間足データをローカルDBに保存しました")
                
                # 時系列順にソート
                self.sort_history_data()
                
                # UIを更新
                self.update_timeframe_options()
                self.update_graph()
            else:
                self.add_log("新しい時間足データはありませんでした")
                
        except Exception as e:
            self.add_log(f"時間足データ取得エラー: {str(e)}", "ERROR")
    
    def fetch_missing_data_from_cloud(self):
        """（無効化）クラウドから欠損データを取得"""
        # 第5段階の実装：リアルタイム欠損補完を削除
        # このメソッドは使用しません
        return
    
    def load_historical_data(self):
        """起動時に過去のデータを読み込む"""
        try:
            cursor = self.conn.cursor()
            
            # 最新の432,000件（300日分）を取得
            cursor.execute("""
                SELECT timestamp, ask_total, bid_total, price
                FROM order_book_history
                ORDER BY timestamp DESC
                LIMIT 432000
            """)
            
            # 古い順に並び替えて履歴に追加
            rows = cursor.fetchall()
            rows.reverse()
            
            loaded_count = 0
            for row in rows:
                timestamp_str, ask_total, bid_total, price = row
                timestamp = datetime.fromisoformat(timestamp_str)
                
                self.time_history.append(timestamp)
                self.ask_history.append(ask_total)
                self.bid_history.append(bid_total)
                loaded_count += 1
            
            if loaded_count > 0:
                self.add_log(f"過去のデータを{loaded_count}件読み込みました")
                # 選択可能な時間足を更新
                self.update_timeframe_options()
                # グラフを更新
                self.update_graph()
            else:
                self.add_log("過去のデータはありません")
            
            # クラウドから各時間足の初期データを取得
            if hasattr(self, 'cloud_sync') and self.cloud_sync and self.cloud_sync.enabled:
                self.add_log("各時間足テーブルから初期データを取得中...")
                self.fetch_initial_timeframe_data()
                
            # 最後に必ず時系列順にソート（クラウドデータと統合後）
            if len(self.time_history) > 0:
                self.sort_history_data()
                self.update_graph()
                
        except Exception as e:
            self.add_log(f"データ読み込みエラー: {str(e)}", "ERROR")
    
    def sort_history_data(self):
        """履歴データを時系列順にソート"""
        if len(self.time_history) > 0:
            # 時系列順にソート
            sorted_data = sorted(zip(self.time_history, self.ask_history, self.bid_history))
            self.time_history = [x[0] for x in sorted_data]
            self.ask_history = [x[1] for x in sorted_data]
            self.bid_history = [x[2] for x in sorted_data]
    
    def update_graph(self):
        """グラフを更新"""
        if len(self.time_history) < 2:
            return  # データが少なすぎる場合は更新しない
        
        try:
            # 時間足に応じたサンプリング間隔を設定
            timeframe = self.timeframe_var.get()
            timeframe_intervals = {
                "1分": 1,
                "3分": 3,
                "5分": 5,
                "15分": 15,
                "30分": 30,
                "1時間": 60,
                "2時間": 120,
                "4時間": 240,
                "1日": 1440
            }
            interval = timeframe_intervals[timeframe]
            
            # 時刻ベースでデータをグループ化
            filtered_times = []
            filtered_asks = []
            filtered_bids = []
            
            # グループ化のための辞書（キー：時間帯、値：その時間帯のデータリスト）
            time_groups = {}
            
            for i in range(len(self.time_history)):
                time_obj = self.time_history[i]
                
                # 時間帯を決定（分単位の間隔に基づく）
                if interval < 60:  # 分足の場合
                    # 指定分単位で切り捨て
                    group_minute = (time_obj.minute // interval) * interval
                    group_key = time_obj.replace(minute=group_minute, second=0, microsecond=0)
                elif interval == 60:  # 1時間足の場合
                    group_key = time_obj.replace(minute=0, second=0, microsecond=0)
                elif interval < 1440:  # 時間足の場合（2時間、4時間）
                    hours_interval = interval // 60
                    group_hour = (time_obj.hour // hours_interval) * hours_interval
                    group_key = time_obj.replace(hour=group_hour, minute=0, second=0, microsecond=0)
                else:  # 日足の場合
                    group_key = time_obj.replace(hour=0, minute=0, second=0, microsecond=0)
                
                # グループにデータを追加
                if group_key not in time_groups:
                    time_groups[group_key] = []
                time_groups[group_key].append((time_obj, self.ask_history[i], self.bid_history[i]))
            
            # 各グループから最後（最新）のデータを選択
            sorted_groups = sorted(time_groups.keys())
            for group_key in sorted_groups:
                # グループ内のデータを時刻でソート
                group_data = sorted(time_groups[group_key], key=lambda x: x[0])
                # 最後のデータを採用（終値）
                last_data = group_data[-1]
                filtered_times.append(last_data[0])
                filtered_asks.append(last_data[1])
                filtered_bids.append(last_data[2])
            
            # 最大300点に制限
            if len(filtered_times) > 300:
                filtered_times = filtered_times[-300:]
                filtered_asks = filtered_asks[-300:]
                filtered_bids = filtered_bids[-300:]
            
            # フィルタリング後にデータが空の場合は処理をスキップ
            if len(filtered_times) < 2:
                return
            
            times = filtered_times
            asks = filtered_asks
            bids = filtered_bids
            
            # 各グラフのY軸範囲を計算
            ask_min = 0
            ask_max = 1
            bid_min = 0
            bid_max = 1
            
            if asks and bids:
                # 各板の最小値・最大値を取得
                min_ask = min(asks)
                min_bid = min(bids)
                max_ask = max(asks)
                max_bid = max(bids)
                
                # 各板の変動幅を計算
                ask_range = max_ask - min_ask
                bid_range = max_bid - min_bid
                
                # より大きい幅を共通幅として採用（最小幅を設定）
                common_range = max(ask_range, bid_range, 1.0)  # 最小幅1.0を保証
                
                # 各グラフの表示範囲を設定（自身の最小値から共通幅分）
                ask_min = min_ask
                ask_max = min_ask + common_range
                bid_min = min_bid
                bid_max = min_bid + common_range
            
            # 売り板グラフを更新
            self.ax_ask.clear()
            self.ax_ask.plot(times, asks, color='#ff6b6b', linewidth=2)
            self.ax_ask.fill_between(times, asks, ask_min, color='#ff6b6b', alpha=0.3)
            self.ax_ask.grid(True, alpha=0.2, color='#444444')
            self.ax_ask.set_facecolor('#1e1e1e')
            self.ax_ask.set_ylim(ask_min, ask_max)
            
            # 売り板のY軸を反転（下向きに表示）
            self.ax_ask.invert_yaxis()
            
            # 買い板グラフを更新
            self.ax_bid.clear()
            self.ax_bid.plot(times, bids, color='#51cf66', linewidth=2)
            self.ax_bid.fill_between(times, bids, bid_min, color='#51cf66', alpha=0.3)
            self.ax_bid.grid(True, alpha=0.2, color='#444444')
            self.ax_bid.set_facecolor('#1e1e1e')
            self.ax_bid.set_ylim(bid_min, bid_max)
            
            # X軸の設定（最大30ラベル、0時は月/日表示）
            for ax in [self.ax_ask, self.ax_bid]:
                # データ点数から間引き間隔を計算（最大30ラベル）
                max_labels = 30
                data_count = len(filtered_times)
                skip_interval = max(1, data_count // max_labels)
                
                # 表示するティックの位置とラベルを準備
                tick_positions = []
                tick_labels = []
                
                for i in range(0, data_count, skip_interval):
                    if i < data_count:
                        tick_positions.append(filtered_times[i])
                        time_obj = filtered_times[i]
                        
                        # 日足の場合はすべて月/日表示
                        if timeframe == "1日":
                            tick_labels.append(f"{time_obj.month}/{time_obj.day}")
                        else:
                            # 0時の場合は月/日表示、それ以外は時間のみ
                            if time_obj.hour == 0 and time_obj.minute == 0:
                                tick_labels.append(f"{time_obj.month}/{time_obj.day}")
                            else:
                                tick_labels.append(f"{time_obj.hour}")
                
                # カスタムティックを設定
                ax.set_xticks(tick_positions)
                ax.set_xticklabels(tick_labels)
                
                # ラベルの回転（必要に応じて）
                if timeframe == "1日" or data_count > 100:
                    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
                else:
                    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha='center')
            
            # グラフを再描画
            self.canvas.draw()
            
        except Exception as e:
            self.add_log(f"グラフ更新エラー: {str(e)}", "ERROR")
        
    
    def clear_all(self):
        """ログとグラフをクリア"""
        # ログをクリア
        self.log_text.delete(1.0, tk.END)
        self.add_log("ログとグラフをクリアしました")
        
        # グラフの履歴データをクリア
        self.time_history = []
        self.ask_history = []
        self.bid_history = []
        
        # グラフを初期状態に戻す
        self.ax_ask.clear()
        self.ax_bid.clear()
        
        # グラフの初期設定を再適用
        self.ax_ask.set_facecolor('#1e1e1e')
        self.ax_ask.grid(True, alpha=0.2, color='#444444')
        self.ax_ask.set_ylim(0, 1)
        self.ax_ask.invert_yaxis()
        
        self.ax_bid.set_facecolor('#1e1e1e')
        self.ax_bid.grid(True, alpha=0.2, color='#444444')
        self.ax_bid.set_ylim(0, 1)
        
        # グラフを再描画
        self.canvas.draw()
        
        # 時間足選択を1分にリセット
        self.timeframe_var.set("1分")
        self.timeframe_combo['values'] = ["1分"]
        
    def scraping_loop(self):
        """スクレイピングループ"""
        self.add_log("スクレイピングを開始しました")
        
        # ヘッドレスモードの設定
        headless = self.headless_var.get()
        if headless:
            self.add_log("ヘッドレスモードで実行中")
        
        # 初回のみページを読み込みとグルーピング設定（ドライバー初期化も含む）
        self.add_log("ページを初期化中...")
        if not self.scraper.initialize_page(headless=headless):
            self.add_log("ページの初期化に失敗しました", "ERROR")
            self.stop_scraping()
            return
        
        self.add_log("初期化完了。データ取得を開始します")
        
        # データ取得ループ
        error_count = 0
        while self.scraper.is_running:
            try:
                # 60秒サイクルの開始
                cycle_start = time.time()
                
                # 15秒待機
                self.add_log("次のデータ取得まで待機中...")
                time.sleep(15)
                
                # 3回取得（15秒、30秒、45秒）
                data_list = []
                for i in range(3):
                    if not self.scraper.is_running:
                        break
                        
                    self.add_log(f"データ取得 {i+1}/3 回目")
                    data = self.scraper.get_order_book_data()
                    data_list.append(data)
                    
                    # 最後の取得でなければ15秒待機
                    if i < 2 and self.scraper.is_running:
                        time.sleep(15)
                
                # 最適値を選定
                if data_list:
                    best_data = self.select_best_values(data_list)
                    if best_data:
                        self.root.after(0, self.update_display, best_data)
                        error_count = 0
                    else:
                        self.add_log("有効なデータが取得できませんでした", "WARNING")
                        error_count += 1
                
                # エラー処理
                if error_count >= 3:
                    self.add_log("連続エラーのため、ページを再初期化します", "WARNING")
                    if self.scraper.initialize_page(headless=headless):
                        self.add_log("再初期化に成功しました")
                        error_count = 0
                    else:
                        self.add_log("再初期化に失敗しました", "ERROR")
                        time.sleep(10)
                
                # 残り時間を待機（60秒サイクルを維持）
                elapsed = time.time() - cycle_start
                remaining = max(0, 60 - elapsed)
                if remaining > 0 and self.scraper.is_running:
                    time.sleep(remaining)
                
            except Exception as e:
                self.add_log(f"エラー: {str(e)}", "ERROR")
                error_count += 1
                
                # セッション切れやページエラーの可能性がある場合
                if "StaleElementReferenceException" in str(e) or "session" in str(e).lower():
                    self.add_log("セッションエラーのため、ページを再初期化します", "WARNING")
                    if self.scraper.initialize_page(headless=headless):
                        self.add_log("再初期化に成功しました")
                        error_count = 0
                
                time.sleep(5)
        
        self.add_log("スクレイピングを停止しました")
        
    def start_scraping(self):
        """スクレイピング開始"""
        self.scraper.is_running = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        self.scraper_thread = threading.Thread(target=self.scraping_loop, daemon=True)
        self.scraper_thread.start()
        
    def stop_scraping(self):
        """スクレイピング停止"""
        self.scraper.is_running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        
        
    def on_closing(self):
        """アプリケーション終了時の処理"""
        # 閉じるボタンを押したら直接トレイに格納
        self.minimize_to_tray()
    
    def quit_app(self):
        """アプリケーションを完全に終了"""
        self.scraper.is_running = False
        self.scraper.close_driver()
        
        # トレイアイコンを停止
        if self.tray_icon:
            self.tray_icon.stop()
        
        # データベース接続を閉じる
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
                self.add_log("データベース接続を閉じました")
        except Exception as e:
            # print(f"データベースクローズエラー: {str(e)}")
            pass
            
        self.root.destroy()
    
    def create_tray_icon(self):
        """システムトレイアイコンを作成"""
        # アイコンファイルが存在する場合は使用、なければデフォルトアイコンを作成
        if os.path.exists('icon.ico'):
            try:
                image = Image.open('icon.ico')
                # 16x16にリサイズ（トレイアイコン用）
                image = image.resize((16, 16), Image.Resampling.LANCZOS)
            except:
                # アイコン読み込みに失敗した場合はデフォルトアイコンを作成
                image = self.create_default_icon()
        else:
            image = self.create_default_icon()
        
        # トレイメニューの作成
        menu = pystray.Menu(
            pystray.MenuItem("表示", self.show_window, default=True),  # defaultをTrueにすることでダブルクリック対応
            pystray.MenuItem("スクレイピング開始", self.tray_start_scraping),
            pystray.MenuItem("スクレイピング停止", self.tray_stop_scraping),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("終了", self.quit_from_tray)
        )
        
        # トレイアイコンの作成
        self.tray_icon = pystray.Icon(
            "CoinglassScraper",
            image,
            "Coinglass Scraper",
            menu
        )
        
        # トレイアイコンをバックグラウンドで実行
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def create_default_icon(self):
        """デフォルトのトレイアイコンを作成"""
        # 16x16のデフォルトアイコンを作成（緑色の四角）
        image = Image.new('RGB', (16, 16), color='green')
        return image
    
    def minimize_to_tray(self):
        """ウィンドウをトレイに最小化"""
        # トレイアイコンがなければ作成
        if not self.tray_icon:
            self.create_tray_icon()
        
        # ウィンドウを非表示にする
        self.root.withdraw()
        self.is_minimized_to_tray = True
        
        # バルーン通知を表示（Windows）
        if platform.system() == "Windows" and self.tray_icon:
            self.tray_icon.notify(
                "Coinglass Scraper",
                "システムトレイに最小化しました"
            )
    
    def show_window(self, icon=None, item=None):
        """トレイから元に戻す"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_minimized_to_tray = False
    
    def tray_start_scraping(self, icon=None, item=None):
        """トレイメニューからスクレイピング開始"""
        if not self.scraper.is_running:
            self.root.after(0, self.start_scraping)
    
    def tray_stop_scraping(self, icon=None, item=None):
        """トレイメニューからスクレイピング停止"""
        if self.scraper.is_running:
            self.root.after(0, self.stop_scraping)
    
    def quit_from_tray(self, icon=None, item=None):
        """トレイメニューから完全終了"""
        self.root.after(0, self.quit_app)
        
    def run(self):
        """アプリケーションを実行"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()


if __name__ == "__main__":
    app = ScraperGUI()
    app.run()