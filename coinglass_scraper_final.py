#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coinglass.com BTC-USDT Order Book Scraper Final Version
実際のページ構造に基づいた正確な板情報取得
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import json
import traceback
import re
import os
import sys
import platform
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class CoinglassScraperFinal:
    def __init__(self):
        self.driver = None
        self.is_running = False
        self.update_interval = 5
        self.url = "https://www.coinglass.com/ja/mergev2/BTC-USDT"
        
        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('coinglass_scraper_final.log', encoding='utf-8'),
                logging.StreamHandler()
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

    def wait_for_order_book(self):
        """オーダーブックの読み込みを待機"""
        try:
            # ページの基本的な読み込みを待つ
            WebDriverWait(self.driver, 30).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # オーダーブックの要素が表示されるまで待つ
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "obv2-item"))
            )
            
            # データが読み込まれるまで少し待つ
            time.sleep(3)
            
            # グルーピングを100に設定
            self.set_grouping_to_100()
            
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

    def get_current_price(self):
        """現在価格を取得"""
        try:
            # 複数の方法で現在価格を探す
            
            # 方法1: 価格表示要素から
            price_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, '104')]")
            if price_elements:
                for elem in price_elements:
                    text = elem.text.strip()
                    if re.match(r'^\d{6}', text):  # 6桁の数字で始まる
                        return float(text.replace(',', ''))
            
            # 方法2: JavaScriptで取得
            current_price = self.driver.execute_script("""
                // 中央の価格を探す
                const priceElements = document.querySelectorAll('.obv2-item-price');
                if (priceElements.length > 0) {
                    const midIndex = Math.floor(priceElements.length / 2);
                    return parseFloat(priceElements[midIndex].textContent.replace(/,/g, ''));
                }
                return null;
            """)
            
            if current_price:
                return current_price
            
            # デフォルト値（スクリーンショットから）
            return 104530.0
            
        except Exception as e:
            self.logger.error(f"現在価格の取得に失敗: {str(e)}")
            return 104530.0  # デフォルト値

    def get_order_book_data(self):
        """売り板と買い板の総量を取得（実際の構造に基づく）"""
        try:
            if not self.driver:
                if not self.setup_driver():
                    return None
            
            # ページを読み込み
            self.driver.get(self.url)
            self.logger.info(f"ページにアクセス: {self.url}")
            
            # オーダーブックの読み込みを待機
            if not self.wait_for_order_book():
                return None
            
            # 現在価格を取得
            current_price = self.get_current_price()
            self.logger.info(f"現在価格: {current_price}")
            
            # 完全な板情報（スクロールして最端のトータル値）を取得
            full_ask_total, full_bid_total = self.get_full_order_book_totals()
            
            # JavaScriptで板情報を取得（表示範囲のみ - 従来の処理）
            order_book_data = self.driver.execute_script("""
                function getOrderBookData(currentPrice) {
                    let askTotal = 0;  // 売り板総量
                    let bidTotal = 0;  // 買い板総量
                    let askCount = 0;
                    let bidCount = 0;
                    
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
                                askCount++;
                            } else if (price < currentPrice) {
                                // 買い板（Bid）
                                bidTotal += amount;
                                bidCount++;
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
                        askCount: askCount,
                        bidCount: bidCount,
                        currentPrice: currentPrice,
                        totalItems: orderItems.length,
                        timestamp: new Date().toISOString()
                    };
                }
                
                return getOrderBookData(arguments[0]);
            """, current_price)
            
            # 追加の検証: テーブルから直接取得
            if order_book_data['askTotal'] == 0 and order_book_data['bidTotal'] == 0:
                order_book_data = self.get_order_book_from_table()
            
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
                           f"買い板総量={order_book_data['bidTotal']:.2f}, "
                           f"売り板数={order_book_data.get('askCount', 0)}, "
                           f"買い板数={order_book_data.get('bidCount', 0)}")
            
            return order_book_data
            
        except Exception as e:
            self.logger.error(f"データ取得エラー: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None

    def get_order_book_from_table(self):
        """テーブル構造から板情報を取得（代替方法）"""
        try:
            # 現在価格を取得
            current_price = self.get_current_price()
            
            ask_total = 0
            bid_total = 0
            ask_count = 0
            bid_count = 0
            
            # XPathで価格と数量を取得
            price_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'obv2-item-price')]")
            amount_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'obv2-item-amount')]")
            
            # 価格と数量のペアを作成
            for i in range(min(len(price_elements), len(amount_elements))):
                try:
                    price_text = price_elements[i].text.strip()
                    amount_text = amount_elements[i].text.strip()
                    
                    if price_text and amount_text:
                        price = float(price_text.replace(',', ''))
                        amount = float(amount_text.replace(',', ''))
                        
                        if price > current_price:
                            ask_total += amount
                            ask_count += 1
                        elif price < current_price:
                            bid_total += amount
                            bid_count += 1
                except:
                    continue
            
            return {
                'askTotal': ask_total,
                'bidTotal': bid_total,
                'askCount': ask_count,
                'bidCount': bid_count,
                'currentPrice': current_price,
                'timestamp': datetime.now().isoformat(),
                'method': 'table'
            }
            
        except Exception as e:
            self.logger.error(f"テーブル抽出エラー: {str(e)}")
            return {
                'askTotal': 0,
                'bidTotal': 0,
                'askCount': 0,
                'bidCount': 0,
                'currentPrice': 0,
                'timestamp': datetime.now().isoformat(),
                'method': 'error'
            }

    def close_driver(self):
        """ドライバーを閉じる"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("ドライバーを終了しました")
            except:
                pass
            self.driver = None


class ScraperGUIFinal:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Coinglass BTC-USDT Order Book Monitor - Final Version")
        self.root.geometry("950x750")
        
        self.scraper = CoinglassScraperFinal()
        self.scraper_thread = None
        self.data_history = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """UIのセットアップ"""
        # スタイル設定
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 18, 'bold'))
        style.configure('Value.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Small.TLabel', font=('Arial', 10))
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タイトル
        title_label = ttk.Label(main_frame, text="BTC-USDT Order Book Monitor", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # 現在の値を表示するフレーム
        value_frame = ttk.LabelFrame(main_frame, text="板情報", padding="15")
        value_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 現在価格
        price_frame = ttk.Frame(value_frame)
        price_frame.grid(row=0, column=0, columnspan=2, pady=5)
        ttk.Label(price_frame, text="現在価格:", font=('Arial', 12)).pack(side=tk.LEFT)
        self.price_label = ttk.Label(price_frame, text="---", font=('Arial', 14, 'bold'))
        self.price_label.pack(side=tk.LEFT, padx=10)
        
        # 売り板総量
        ask_frame = ttk.Frame(value_frame)
        ask_frame.grid(row=1, column=0, padx=20, pady=5)
        ttk.Label(ask_frame, text="売り板総量:", font=('Arial', 12)).pack()
        self.ask_label = ttk.Label(ask_frame, text="---", style='Value.TLabel', foreground='red')
        self.ask_label.pack()
        self.ask_count_label = ttk.Label(ask_frame, text="(0件)", style='Small.TLabel')
        self.ask_count_label.pack()
        
        # 買い板総量
        bid_frame = ttk.Frame(value_frame)
        bid_frame.grid(row=1, column=1, padx=20, pady=5)
        ttk.Label(bid_frame, text="買い板総量:", font=('Arial', 12)).pack()
        self.bid_label = ttk.Label(bid_frame, text="---", style='Value.TLabel', foreground='green')
        self.bid_label.pack()
        self.bid_count_label = ttk.Label(bid_frame, text="(0件)", style='Small.TLabel')
        self.bid_count_label.pack()
        
        # 比率と差額
        ratio_frame = ttk.Frame(value_frame)
        ratio_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Label(ratio_frame, text="買い/売り比率:", font=('Arial', 12)).pack(side=tk.LEFT)
        self.ratio_label = ttk.Label(ratio_frame, text="---", font=('Arial', 14, 'bold'))
        self.ratio_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(ratio_frame, text="差額:", font=('Arial', 12)).pack(side=tk.LEFT, padx=20)
        self.diff_label = ttk.Label(ratio_frame, text="---", font=('Arial', 14, 'bold'))
        self.diff_label.pack(side=tk.LEFT, padx=10)
        
        # 最終更新時刻
        info_frame = ttk.Frame(value_frame)
        info_frame.grid(row=3, column=0, columnspan=2, pady=5)
        self.time_label = ttk.Label(info_frame, text="最終更新: ---", font=('Arial', 10))
        self.time_label.pack()
        
        # コントロールボタン
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="開始", command=self.start_scraping,
                                      width=15)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="停止", command=self.stop_scraping, 
                                     state='disabled', width=15)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        self.screenshot_button = ttk.Button(control_frame, text="スクリーンショット", 
                                           command=self.take_screenshot, width=15)
        self.screenshot_button.grid(row=0, column=2, padx=5)
        
        self.export_button = ttk.Button(control_frame, text="データエクスポート", 
                                       command=self.export_data, width=15)
        self.export_button.grid(row=0, column=3, padx=5)
        
        # 設定フレーム
        settings_frame = ttk.LabelFrame(main_frame, text="設定", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(settings_frame, text="更新間隔(秒):").grid(row=0, column=0, padx=5)
        self.interval_var = tk.StringVar(value="5")
        interval_spinbox = ttk.Spinbox(settings_frame, from_=1, to=60, width=10, 
                                      textvariable=self.interval_var)
        interval_spinbox.grid(row=0, column=1, padx=5)
        
        self.headless_var = tk.BooleanVar(value=False)
        headless_check = ttk.Checkbutton(settings_frame, text="ヘッドレスモード", 
                                        variable=self.headless_var)
        headless_check.grid(row=0, column=2, padx=20)
        
        # ログ表示エリア
        log_frame = ttk.LabelFrame(main_frame, text="ログ", padding="5")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=110)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッドの重み設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def update_display(self, data):
        """表示を更新"""
        if data and data.get('askTotal', 0) > 0 or data.get('bidTotal', 0) > 0:
            ask_total = data.get('askTotal', 0)
            bid_total = data.get('bidTotal', 0)
            current_price = data.get('currentPrice', 0)
            ask_count = data.get('askCount', 0)
            bid_count = data.get('bidCount', 0)
            
            # 現在価格
            if current_price > 0:
                self.price_label.config(text=f"{current_price:,.0f}")
            
            # 売り板・買い板（完全な板情報を優先表示）
            full_ask_total = data.get('fullAskTotal', ask_total)
            full_bid_total = data.get('fullBidTotal', bid_total)
            
            self.ask_label.config(text=f"{full_ask_total:,.2f}")
            self.bid_label.config(text=f"{full_bid_total:,.2f}")
            self.ask_count_label.config(text=f"({ask_count}件)")
            self.bid_count_label.config(text=f"({bid_count}件)")
            
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
            
            self.time_label.config(text=f"最終更新: {datetime.now().strftime('%H:%M:%S')}")
            
            log_message = (f"更新成功: 売り板={full_ask_total:,.2f}({ask_count}件), "
                          f"買い板={full_bid_total:,.2f}({bid_count}件), "
                          f"現在価格={current_price:,.0f}")
            self.add_log(log_message)
            
            # 履歴に追加
            self.data_history.append(data)
            if len(self.data_history) > 1000:  # 最新1000件のみ保持
                self.data_history.pop(0)
        else:
            self.add_log("データ取得に失敗しました（板情報が空です）", "WARNING")
    
    def add_log(self, message, level="INFO"):
        """ログを追加"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
    def take_screenshot(self):
        """スクリーンショットを撮影"""
        if self.scraper.driver:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.scraper.driver.save_screenshot(filename)
            self.add_log(f"スクリーンショットを保存しました: {filename}")
            messagebox.showinfo("スクリーンショット", f"スクリーンショットを保存しました:\n{filename}")
        else:
            messagebox.showwarning("警告", "ドライバーが起動していません")
        
    def scraping_loop(self):
        """スクレイピングループ"""
        self.add_log("スクレイピングを開始しました")
        
        # ヘッドレスモードの設定
        headless = self.headless_var.get()
        if headless:
            self.add_log("ヘッドレスモードで実行中")
        
        # ドライバーを初期化
        if not self.scraper.setup_driver(headless=headless):
            self.add_log("ドライバーの初期化に失敗しました", "ERROR")
            self.stop_scraping()
            return
        
        while self.scraper.is_running:
            try:
                data = self.scraper.get_order_book_data()
                self.root.after(0, self.update_display, data)
                
                # 指定された間隔で待機
                interval = int(self.interval_var.get())
                time.sleep(interval)
                
            except Exception as e:
                self.add_log(f"エラー: {str(e)}", "ERROR")
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
        
    def export_data(self):
        """データをエクスポート"""
        if self.data_history:
            filename = f"order_book_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.data_history, f, indent=2, ensure_ascii=False)
            
            # CSV形式でもエクスポート
            csv_filename = f"order_book_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(csv_filename, 'w', encoding='utf-8') as f:
                f.write("Timestamp,Current Price,Ask Total,Ask Count,Bid Total,Bid Count,Ratio\n")
                for item in self.data_history:
                    ratio = item['bidTotal'] / item['askTotal'] if item['askTotal'] > 0 else 0
                    f.write(f"{item['timestamp']},{item.get('currentPrice', 0)},"
                           f"{item['askTotal']},{item.get('askCount', 0)},"
                           f"{item['bidTotal']},{item.get('bidCount', 0)},"
                           f"{ratio:.3f}\n")
            
            self.add_log(f"データをエクスポートしました: {filename}, {csv_filename}")
            messagebox.showinfo("エクスポート", 
                              f"データをエクスポートしました:\n{filename}\n{csv_filename}")
        else:
            messagebox.showwarning("警告", "エクスポートするデータがありません")
        
    def on_closing(self):
        """アプリケーション終了時の処理"""
        self.scraper.is_running = False
        self.scraper.close_driver()
        self.root.destroy()
        
    def run(self):
        """アプリケーションを実行"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()


if __name__ == "__main__":
    app = ScraperGUIFinal()
    app.run()