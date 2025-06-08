#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coinglass スクロールエリア調査スクリプト
売り板・買い板のスクロール可能な要素を特定する
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_scroll_areas():
    """スクロールエリアの要素を調査"""
    # Chrome設定
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        print(f"Chrome起動エラー: {str(e)}")
        return
    
    try:
        print("ページにアクセス中...")
        driver.get("https://www.coinglass.com/ja/mergev2/BTC-USDT")
        time.sleep(5)
        
        # グルーピングを100に設定
        print("\nグルーピングを100に設定中...")
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, "button.MuiSelect-button")
            for button in buttons:
                if button.text.strip() in ['10', '50', '100'] and button.is_displayed():
                    if button.text.strip() != '100':
                        button.click()
                        time.sleep(1)
                        option_100 = driver.find_element(By.XPATH, "//li[text()='100']")
                        option_100.click()
                        time.sleep(2)
                    break
        except:
            print("グルーピング設定をスキップ")
        
        print("\n=== スクロール可能な要素を探索 ===")
        
        # JavaScriptでスクロール可能な要素を探す
        scrollable_elements = driver.execute_script("""
            const elements = document.querySelectorAll('*');
            const scrollables = [];
            
            for (let elem of elements) {
                const style = window.getComputedStyle(elem);
                const isScrollable = (
                    style.overflow === 'scroll' || 
                    style.overflow === 'auto' ||
                    style.overflowY === 'scroll' || 
                    style.overflowY === 'auto'
                );
                
                if (isScrollable && elem.scrollHeight > elem.clientHeight) {
                    scrollables.push({
                        tag: elem.tagName,
                        className: elem.className,
                        id: elem.id,
                        scrollHeight: elem.scrollHeight,
                        clientHeight: elem.clientHeight,
                        innerHTML: elem.innerHTML.substring(0, 100)
                    });
                }
            }
            
            return scrollables;
        """)
        
        print(f"スクロール可能な要素数: {len(scrollable_elements)}")
        for i, elem in enumerate(scrollable_elements):
            print(f"\n要素 {i+1}:")
            print(f"  タグ: {elem['tag']}")
            print(f"  クラス: {elem['className']}")
            print(f"  ID: {elem['id']}")
            print(f"  スクロール高さ: {elem['scrollHeight']}px")
            print(f"  表示高さ: {elem['clientHeight']}px")
        
        print("\n=== 板情報の構造を分析 ===")
        
        # 板情報の要素を探す
        board_analysis = driver.execute_script("""
            // 価格・数量・トータルの要素を探す
            const priceElems = document.querySelectorAll('.obv2-item-price');
            const amountElems = document.querySelectorAll('.obv2-item-amount');
            
            // 売り板・買い板のコンテナを探す
            let askContainer = null;
            let bidContainer = null;
            
            // 現在価格の要素を探す
            const currentPriceElem = document.querySelector('.Number');
            let currentPrice = 0;
            if (currentPriceElem) {
                currentPrice = parseFloat(currentPriceElem.textContent.replace(/,/g, ''));
            }
            
            // 各要素の親要素を遡ってコンテナを特定
            if (priceElems.length > 0) {
                for (let elem of priceElems) {
                    const price = parseFloat(elem.textContent.replace(/,/g, ''));
                    let parent = elem.parentElement;
                    
                    // 親要素を遡る（最大10階層）
                    for (let i = 0; i < 10; i++) {
                        if (!parent) break;
                        
                        const style = window.getComputedStyle(parent);
                        if (style.overflowY === 'scroll' || style.overflowY === 'auto') {
                            if (price > currentPrice && !askContainer) {
                                askContainer = parent;
                            } else if (price < currentPrice && !bidContainer) {
                                bidContainer = parent;
                            }
                            break;
                        }
                        parent = parent.parentElement;
                    }
                }
            }
            
            // obv2関連のクラスを持つ要素も確認
            const obv2Elements = document.querySelectorAll('[class*="obv2"]');
            const obv2Info = [];
            for (let elem of obv2Elements) {
                if (elem.className.includes('obv2')) {
                    obv2Info.push({
                        className: elem.className,
                        tag: elem.tagName,
                        hasScroll: elem.scrollHeight > elem.clientHeight
                    });
                }
            }
            
            return {
                currentPrice: currentPrice,
                priceCount: priceElems.length,
                amountCount: amountElems.length,
                askContainer: askContainer ? {
                    tag: askContainer.tagName,
                    className: askContainer.className,
                    id: askContainer.id
                } : null,
                bidContainer: bidContainer ? {
                    tag: bidContainer.tagName,
                    className: bidContainer.className,
                    id: bidContainer.id
                } : null,
                obv2Elements: obv2Info.slice(0, 10)  // 最初の10個まで
            };
        """)
        
        print(f"現在価格: {board_analysis['currentPrice']}")
        print(f"価格要素数: {board_analysis['priceCount']}")
        print(f"数量要素数: {board_analysis['amountCount']}")
        
        if board_analysis['askContainer']:
            print(f"\n売り板コンテナ:")
            print(f"  タグ: {board_analysis['askContainer']['tag']}")
            print(f"  クラス: {board_analysis['askContainer']['className']}")
        
        if board_analysis['bidContainer']:
            print(f"\n買い板コンテナ:")
            print(f"  タグ: {board_analysis['bidContainer']['tag']}")
            print(f"  クラス: {board_analysis['bidContainer']['className']}")
        
        print(f"\nobv2関連要素:")
        for elem in board_analysis['obv2Elements'][:5]:
            print(f"  {elem['tag']}.{elem['className']} (スクロール: {elem['hasScroll']})")
        
        print("\n=== 実際にスクロールをテスト ===")
        
        # スクロール可能な要素を見つけてテスト
        test_scroll = driver.execute_script("""
            // 最も可能性の高いスクロールコンテナを探す
            const candidates = document.querySelectorAll('.obv2-orderbook, [class*="orderbook"], [class*="depth"]');
            let scrolled = false;
            
            for (let elem of candidates) {
                if (elem.scrollHeight > elem.clientHeight) {
                    // 上にスクロール
                    const originalTop = elem.scrollTop;
                    elem.scrollTop = 0;
                    const scrolledToTop = elem.scrollTop === 0;
                    
                    // 下にスクロール
                    elem.scrollTop = elem.scrollHeight;
                    const scrolledToBottom = elem.scrollTop > originalTop;
                    
                    // 元に戻す
                    elem.scrollTop = originalTop;
                    
                    if (scrolledToTop || scrolledToBottom) {
                        return {
                            success: true,
                            element: {
                                tag: elem.tagName,
                                className: elem.className,
                                id: elem.id,
                                scrollHeight: elem.scrollHeight,
                                clientHeight: elem.clientHeight
                            }
                        };
                    }
                }
            }
            
            return { success: false };
        """)
        
        if test_scroll['success']:
            print("スクロール可能な要素を発見:")
            print(f"  タグ: {test_scroll['element']['tag']}")
            print(f"  クラス: {test_scroll['element']['className']}")
            print(f"  スクロール可能高さ: {test_scroll['element']['scrollHeight'] - test_scroll['element']['clientHeight']}px")
        else:
            print("明確なスクロールコンテナが見つかりませんでした")
        
        input("\n\nEnterキーを押すと終了します...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_scroll_areas()