#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CoinGlass価格表示要素調査ツール
Binanceの正確な価格表示を取得するためのHTML構造を調査
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PriceAnalyzer:
    def __init__(self):
        self.driver = None
        self.url = "https://www.coinglass.com/ja/mergev2/BTC-USDT"
        
    def setup_driver(self):
        """Chromeドライバーのセットアップ"""
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        logger.info("ChromeDriverを起動しました")
        
    def load_page(self):
        """ページを読み込み"""
        logger.info(f"ページを読み込み中: {self.url}")
        self.driver.get(self.url)
        time.sleep(5)  # ページの完全読み込みを待つ
        
    def analyze_price_elements(self):
        """価格表示要素を分析"""
        results = {
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "price_elements": [],
            "potential_selectors": []
        }
        
        logger.info("価格表示要素を検索中...")
        
        # 1. 売り板と買い板の間のエリアを探す
        try:
            # 板の間の中央エリアを探す
            middle_areas = self.driver.find_elements(By.CSS_SELECTOR, 
                "[class*='middle'], [class*='center'], [class*='price'], [class*='current']")
            
            for area in middle_areas:
                if area.is_displayed():
                    text = area.text.strip()
                    if text and any(char.isdigit() for char in text):
                        element_info = {
                            "selector": f"CSS: {area.get_attribute('class')}",
                            "text": text,
                            "tag": area.tag_name,
                            "class": area.get_attribute('class'),
                            "id": area.get_attribute('id') or "なし"
                        }
                        results["price_elements"].append(element_info)
                        logger.info(f"価格候補発見: {text}")
        except Exception as e:
            logger.error(f"中央エリア検索エラー: {e}")
        
        # 2. 数値を含む要素を幅広く検索
        try:
            # 小数点を含む数値パターンを検索
            all_elements = self.driver.find_elements(By.XPATH, 
                "//*[contains(text(), '.') and string-length(text()) > 5 and string-length(text()) < 15]")
            
            for elem in all_elements:
                try:
                    text = elem.text.strip()
                    # 価格のような形式（例: 105101.8）をチェック
                    if text and '.' in text and text.replace('.', '').replace(',', '').isdigit():
                        # 10万以上の数値（BTCの価格帯）
                        try:
                            value = float(text.replace(',', ''))
                            if 50000 < value < 200000:  # BTCの妥当な価格範囲
                                element_info = {
                                    "xpath": self.get_xpath(elem),
                                    "text": text,
                                    "tag": elem.tag_name,
                                    "class": elem.get_attribute('class') or "なし",
                                    "parent_class": elem.find_element(By.XPATH, '..').get_attribute('class') if elem.find_element(By.XPATH, '..') else "なし",
                                    "location": elem.location,
                                    "size": elem.size
                                }
                                results["price_elements"].append(element_info)
                                logger.info(f"価格候補（数値）: {text}")
                        except ValueError:
                            pass
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"数値要素検索エラー: {e}")
        
        # 3. JavaScriptで価格要素を探す
        try:
            js_results = self.driver.execute_script("""
                const results = [];
                
                // すべての要素をチェック
                const allElements = document.querySelectorAll('*');
                
                for (const elem of allElements) {
                    const text = elem.textContent.trim();
                    
                    // 価格のような形式をチェック
                    if (text && text.includes('.') && text.length > 5 && text.length < 15) {
                        const cleanText = text.replace(/,/g, '');
                        const numValue = parseFloat(cleanText);
                        
                        // BTCの価格範囲内かチェック
                        if (!isNaN(numValue) && numValue > 50000 && numValue < 200000) {
                            // 子要素のテキストを除外して、この要素固有のテキストのみ取得
                            const ownText = Array.from(elem.childNodes)
                                .filter(node => node.nodeType === Node.TEXT_NODE)
                                .map(node => node.textContent.trim())
                                .join(' ');
                            
                            if (ownText.includes('.')) {
                                results.push({
                                    text: ownText,
                                    fullText: text,
                                    tagName: elem.tagName,
                                    className: elem.className,
                                    id: elem.id,
                                    selector: elem.className ? `.${elem.className.split(' ').join('.')}` : elem.tagName,
                                    rect: elem.getBoundingClientRect(),
                                    computed: {
                                        fontSize: window.getComputedStyle(elem).fontSize,
                                        fontWeight: window.getComputedStyle(elem).fontWeight,
                                        color: window.getComputedStyle(elem).color
                                    }
                                });
                            }
                        }
                    }
                }
                
                return results;
            """)
            
            for js_elem in js_results:
                results["price_elements"].append({
                    "source": "JavaScript",
                    **js_elem
                })
                logger.info(f"JS価格候補: {js_elem['text']}")
                
        except Exception as e:
            logger.error(f"JavaScript検索エラー: {e}")
        
        # 4. 推奨セレクタを生成
        for elem in results["price_elements"]:
            if "class" in elem and elem["class"]:
                classes = elem["class"].split()
                for cls in classes:
                    if any(keyword in cls.lower() for keyword in ['price', 'current', 'ticker', 'value']):
                        results["potential_selectors"].append(f".{cls}")
        
        return results
    
    def get_xpath(self, element):
        """要素のXPathを取得"""
        try:
            return self.driver.execute_script("""
                function getXPath(element) {
                    if (element.id !== '')
                        return '//*[@id="' + element.id + '"]';
                    if (element === document.body)
                        return element.tagName;
                    
                    var ix = 0;
                    var siblings = element.parentNode.childNodes;
                    for (var i = 0; i < siblings.length; i++) {
                        var sibling = siblings[i];
                        if (sibling === element)
                            return getXPath(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                            ix++;
                    }
                }
                return getXPath(arguments[0]);
            """, element)
        except:
            return "XPath取得失敗"
    
    def save_results(self, results):
        """結果を保存"""
        timestamp = results["timestamp"]
        filename = f"price_analysis_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"結果を保存しました: {filename}")
        
        # 画面のスクリーンショットも保存
        screenshot_name = f"price_screenshot_{timestamp}.png"
        self.driver.save_screenshot(screenshot_name)
        logger.info(f"スクリーンショットを保存しました: {screenshot_name}")
        
    def run(self):
        """メイン実行"""
        try:
            self.setup_driver()
            self.load_page()
            
            logger.info("Enter を押して分析を開始してください...")
            input()
            
            results = self.analyze_price_elements()
            
            logger.info(f"\n価格要素候補を {len(results['price_elements'])} 個発見しました")
            logger.info(f"推奨セレクタ: {results['potential_selectors']}")
            
            self.save_results(results)
            
            logger.info("\n結果をファイルに保存しました。")
            logger.info("ブラウザは開いたままです。手動で確認してください。")
            logger.info("終了するには Enter を押してください...")
            input()
            
        except Exception as e:
            logger.error(f"エラーが発生しました: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("ドライバーを終了しました")

if __name__ == "__main__":
    analyzer = PriceAnalyzer()
    analyzer.run()