#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coinglass グルーピング機能テストスクリプト
プルダウンメニューの要素を詳しく調査する
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

def test_grouping():
    """グルーピングプルダウンの要素を調査"""
    # Chrome設定
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        print(f"Chrome起動エラー: {str(e)}")
        print("ChromeDriverがPATHに設定されているか確認してください")
        return
    
    try:
        print("ページにアクセス中...")
        driver.get("https://www.coinglass.com/ja/mergev2/BTC-USDT")
        time.sleep(5)
        
        print("\n=== すべてのボタン要素 ===")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for i, btn in enumerate(buttons):
            text = btn.text.strip()
            if text:  # テキストがあるボタンのみ表示
                print(f"Button {i}: '{text}' - Class: {btn.get_attribute('class')}")
        
        print("\n=== MuiSelect関連要素 ===")
        select_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='MuiSelect']")
        print(f"MuiSelect要素数: {len(select_elements)}")
        for i, elem in enumerate(select_elements):
            print(f"  {i}: Tag={elem.tag_name}, Class={elem.get_attribute('class')}, Text='{elem.text}'")
        
        print("\n=== グルーピングボタンの詳細 ===")
        # 複数の方法で探す
        selectors = [
            ("button.MuiSelect-button", "CSS: button.MuiSelect-button"),
            ("//button[contains(@class, 'MuiSelect-button')]", "XPath: contains MuiSelect-button"),
            ("//button[text()='10' or text()='50' or text()='100']", "XPath: text 10/50/100"),
        ]
        
        for selector, description in selectors:
            try:
                if description.startswith("CSS"):
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                else:
                    elements = driver.find_elements(By.XPATH, selector)
                print(f"\n{description}: {len(elements)}個見つかりました")
                for elem in elements:
                    print(f"  - Text: '{elem.text}', Displayed: {elem.is_displayed()}, Enabled: {elem.is_enabled()}")
                    print(f"    aria-expanded: {elem.get_attribute('aria-expanded')}")
                    print(f"    Location: {elem.location}")
            except Exception as e:
                print(f"\n{description}: エラー - {str(e)}")
        
        print("\n=== JavaScriptでの要素確認 ===")
        js_result = driver.execute_script("""
            const buttons = document.querySelectorAll('button');
            let groupingButton = null;
            
            for (let btn of buttons) {
                if (btn.textContent === '10' || btn.textContent === '50' || btn.textContent === '100') {
                    groupingButton = btn;
                    break;
                }
            }
            
            if (groupingButton) {
                return {
                    found: true,
                    text: groupingButton.textContent,
                    className: groupingButton.className,
                    parentClassName: groupingButton.parentElement.className,
                    xpath: (function(el) {
                        if (el.id) return 'id("' + el.id + '")';
                        var path = '';
                        while (el && el.nodeType === 1) {
                            var index = 0;
                            for (var sibling = el.previousSibling; sibling; sibling = sibling.previousSibling) {
                                if (sibling.nodeType === 1 && sibling.tagName === el.tagName) index++;
                            }
                            path = '/' + el.tagName + '[' + (index + 1) + ']' + path;
                            el = el.parentNode;
                        }
                        return path;
                    })(groupingButton)
                };
            }
            return { found: false };
        """)
        
        if js_result['found']:
            print(f"JavaScriptでグルーピングボタンを発見:")
            print(f"  Text: {js_result['text']}")
            print(f"  Class: {js_result['className']}")
            print(f"  Parent Class: {js_result['parentClassName']}")
            print(f"  XPath: {js_result['xpath']}")
        else:
            print("JavaScriptでグルーピングボタンが見つかりませんでした")
        
        print("\n=== テスト: プルダウンをクリック ===")
        try:
            # 最も可能性の高い方法でボタンを探す
            button = driver.find_element(By.CSS_SELECTOR, "button.MuiSelect-button")
            print(f"ボタンを発見: '{button.text}'")
            
            # クリック前の状態
            print(f"クリック前 - aria-expanded: {button.get_attribute('aria-expanded')}")
            
            # クリック
            button.click()
            time.sleep(1)
            
            # クリック後の状態
            print(f"クリック後 - aria-expanded: {button.get_attribute('aria-expanded')}")
            
            # オプションメニューを探す
            print("\n=== オプションメニューの要素 ===")
            option_selectors = [
                ("li[role='option']", "CSS: li[role='option']"),
                ("//li[@role='option']", "XPath: li[@role='option']"),
                ("[role='listbox'] li", "CSS: [role='listbox'] li"),
                ("div[role='presentation'] li", "CSS: div[role='presentation'] li"),
            ]
            
            for selector, description in option_selectors:
                try:
                    if description.startswith("CSS"):
                        options = driver.find_elements(By.CSS_SELECTOR, selector)
                    else:
                        options = driver.find_elements(By.XPATH, selector)
                    if options:
                        print(f"\n{description}: {len(options)}個のオプション")
                        for opt in options[:5]:  # 最初の5個まで表示
                            print(f"  - '{opt.text}'")
                except:
                    pass
            
        except Exception as e:
            print(f"プルダウンクリックエラー: {str(e)}")
        
        input("\n\nEnterキーを押すと終了します...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_grouping()