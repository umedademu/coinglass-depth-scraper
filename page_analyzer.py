#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coinglass.com ページ構造分析ツール
実際のHTML構造を分析して板情報の場所を特定
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from datetime import datetime
import os

def analyze_page():
    """ページ構造を詳細に分析"""
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print("ページにアクセスしています...")
        driver.get("https://www.coinglass.com/ja/mergev2/BTC-USDT")
        
        # ページ読み込み待機
        time.sleep(10)
        
        # スクリーンショット保存
        screenshot_name = f"page_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        driver.save_screenshot(screenshot_name)
        print(f"スクリーンショットを保存: {screenshot_name}")
        
        # ページのHTML全体を保存
        html_name = f"page_source_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(html_name, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"HTMLソースを保存: {html_name}")
        
        # すべての要素のテキストを取得
        all_text = driver.find_element(By.TAG_NAME, 'body').text
        text_name = f"page_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(text_name, 'w', encoding='utf-8') as f:
            f.write(all_text)
        print(f"ページテキストを保存: {text_name}")
        
        # 数値を含む要素を探す
        print("\n数値を含む要素を検索中...")
        elements_with_numbers = []
        
        # すべての要素を取得
        all_elements = driver.find_elements(By.XPATH, "//*[text()]")
        
        for element in all_elements:
            try:
                text = element.text.strip()
                if text and any(char.isdigit() for char in text):
                    # 要素の情報を収集
                    element_info = {
                        'text': text,
                        'tag': element.tag_name,
                        'class': element.get_attribute('class'),
                        'id': element.get_attribute('id'),
                        'style': element.get_attribute('style'),
                        'xpath': driver.execute_script("""
                            function getXPath(element) {
                                if (element.id !== '')
                                    return 'id("' + element.id + '")';
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
                    }
                    elements_with_numbers.append(element_info)
            except:
                pass
        
        # 結果を保存
        analysis_name = f"page_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(analysis_name, 'w', encoding='utf-8') as f:
            json.dump(elements_with_numbers, f, ensure_ascii=False, indent=2)
        print(f"分析結果を保存: {analysis_name}")
        
        # 特定のパターンを探す
        print("\n板情報と思われる要素を検索中...")
        
        # よくある板情報のパターン
        patterns = [
            "売り", "売板", "Ask", "Sell", "ASK",
            "買い", "買板", "Bid", "Buy", "BID",
            "総量", "Total", "Sum", "Volume"
        ]
        
        for pattern in patterns:
            matching_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{pattern}')]")
            if matching_elements:
                print(f"\n'{pattern}'を含む要素が{len(matching_elements)}個見つかりました:")
                for elem in matching_elements[:5]:  # 最初の5個まで表示
                    try:
                        print(f"  - Text: {elem.text[:100]}")
                        print(f"    Tag: {elem.tag_name}, Class: {elem.get_attribute('class')}")
                    except:
                        pass
        
        # JavaScriptでデータ構造を探索
        print("\nJavaScriptでデータ構造を探索中...")
        js_result = driver.execute_script("""
            // グローバル変数を探索
            let results = {};
            
            // windowオブジェクトのプロパティを探す
            for (let key in window) {
                try {
                    let value = window[key];
                    if (typeof value === 'object' && value !== null) {
                        let str = JSON.stringify(value);
                        if (str && (str.includes('ask') || str.includes('bid') || 
                                   str.includes('buy') || str.includes('sell'))) {
                            results[key] = str.substring(0, 200) + '...';
                        }
                    }
                } catch(e) {}
            }
            
            // React/Vueのデータを探す
            let reactData = document.querySelector('[data-reactroot]');
            if (reactData) results['hasReact'] = true;
            
            let vueData = document.querySelector('[data-v-]');
            if (vueData) results['hasVue'] = true;
            
            return results;
        """)
        
        if js_result:
            js_name = f"js_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(js_name, 'w', encoding='utf-8') as f:
                json.dump(js_result, f, ensure_ascii=False, indent=2)
            print(f"JavaScript分析結果を保存: {js_name}")
        
        print("\n分析完了！保存されたファイルを確認してください。")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_page()