# 撤去工事見積ページ実装計画

## 📌 このドキュメントについて

これは撤去工事見積ページ（`/estimates/demolition`）の実装を段階的に進めるための計画書です。
各段階で動作確認を行いながら、仕様書の精度を高めていく開発手法を採用しています。

**重要**: 実装を始める前に、必ずこのドキュメント全体を読んでください。

**実装状況**: 
- 第1段階：基本フレームワークの構築 ✅ 完了
- 第2段階：基本的なブロック構造の生成 ✅ 完了
- 第3段階：計算ロジックとの連携 ✅ 完了
- 第4段階：各見積データの小計表示 ✅ 完了
- 第5段階：調整値機能の実装 ✅ 完了

## 🎯 実装方針

1. **段階的実装**: 5つの段階に分けて、各段階で動作確認を行う
2. **仕様書駆動開発**: 実装から得た知見を仕様書にフィードバックする
3. **既存構造の踏襲**: 擁壁見積ページ（`/estimates/retaining-wall`）の構造を完全に踏襲する
4. **トライアンドエラー**: 各段階で問題を発見し、仕様書を改善する

## 📍 実装の前提条件

**重要**: 撤去工事見積ページの実装を開始する際は、以下の前提条件が満たされています：

### テストデータは必ず存在します
- 撤去工事入力ページ（/demolition-input）で既に複数のテストデータが作成・保存済み
- 「撤去テストA」「撤去テストB」などの見積データが存在
- **新規にテストデータを作成する必要はありません**
- **データが存在しないと判断して新規作成を始めないでください**

この前提に基づいて実装を進めてください。

## ⚠️ 仕様書記載ルール

**重要**: 仕様書には進捗状況のメモ（「完了」「✅」「[x]」など）を記載しないこと。
仕様書は常に「これから実装する」前提で記述し、実装の進捗管理は別途行う。

## ⚠️ データキー名に関する重要なルール

**【重要】データのキー名は入力ページで保存されたものをそのまま使用すること。**
- `estimateData.demolitionMachine1`（バックホー）
- `estimateData.demolitionMachine2`（使用機種）  
- `estimateData.disposalVehicle`（残土搬出車両）
- `estimateData.concrete`（生コン）
- `estimateData.cutter`（カッター）
- `estimateData.distance`（距離）
- `estimateData.width`（幅）
- `estimateData.thickness`（厚さ）
- `estimateData.cutterPitch`（カッターピッチ）
- `estimateData.dumpRotations`（1日ダンプの回転数）

**独自のキー名を作成しないこと。必ず上記のキー名を使用する。**

## 📋 実装段階

### 第1段階：基本フレームワークの構築

#### 目標
見積ページの骨組みを作成し、保存済みデータの基本的な表示を実現する。

#### タスク
- `/app/estimates/retaining-wall/page.tsx`をコピーして`demolition/page.tsx`を作成
- estimateType === 'demolition'でフィルタリング処理を実装
- demolitionEstimateGenerator.tsの骨組みを作成（空配列を返す）
- GrandSummary（総合計）の枠組みを表示
- 基本的な動作確認

#### 確認項目
```
- /estimates/demolitionにアクセスできる
- 保存済みの撤去工事見積が一覧表示される
- 見積カードに名前と日付が表示される
- 総合計の枠が表示される（金額は0円でOK）
```

#### 実装時のメモ
- retaining-wallページをベースに最小限の実装を作成
- ヘッダーカラーは既存3ページと同じ青系（from-blue-700 via-indigo-800 to-purple-800）を適用
- 自動保存機能は第1段階では未実装（骨組みのみ）
- generateBlocksFromEstimateは空配列を返す実装
- 撤去工事見積がない場合は「新規作成」ボタンで/demolition-inputへ遷移

---

### 第2段階：基本的なブロック構造の生成 【2025年7月実装完了】

#### 目標
3つのブロック（カッター工事、撤去工事、廃材搬出）を正しい階層で表示する。

#### タスク
- demolitionEstimateGenerator.tsで3つの空ブロックを生成
- 各ブロックのIDと名前を設定
- ブロックの展開/折りたたみ機能の確認
- ブロックヘッダーの色設定（仕様書通り）

#### 確認項目
```
- 見積カード内に3つのブロックが表示される
- 各ブロックが展開/折りたたみできる
- ブロック名が正しく表示される
- ブロックの色が仕様通り（紫、インディゴ、アンバー）
```

#### 実装時の詳細仕様

##### 1. demolitionEstimateGenerator.tsでのブロック生成
```typescript
// ブロックID生成ルール
id: generateDeterministicId(estimateData.id || 'demolition', 'cutter')
// 第2引数は type: 'cutter' | 'demolition' | 'disposal'

// ブロック構造
{
  id: string,
  type: 'cutter' | 'demolition' | 'disposal',
  name: string,
  isExpanded: true,  // 初期状態は展開
  items: [],         // 第2段階では空配列
  totalAmount: 0,    // 第2段階では0
  color: string      // 'purple' | 'indigo' | 'amber'
}
```

##### 2. DemolitionEstimateBlockコンポーネントの仕様
- **注意**: 第3-5段階でBaseEstimateBlockを使用するため、DemolitionEstimateBlockは作成しません
- **使用するコンポーネント**: `/app/components/common/BaseEstimateBlock.tsx`
- **参考実装**: `/app/components/retaining-wall/RetainingWallEstimateBlock.tsx`

- **色の具体的なTailwindクラス**:
  - カッター工事（purple）:
    - 背景: `from-purple-100/90 via-purple-50/60 to-slate-50/70`
    - ホバー: `hover:from-purple-200/80 hover:via-purple-100/70 hover:to-slate-100/60`
    - テキスト: `from-purple-800 via-purple-700 to-violet-700`
    - アイコン: `text-purple-700`
  - 撤去工事（indigo）:
    - 背景: `from-indigo-100/90 via-indigo-50/60 to-slate-50/70`
    - ホバー: `hover:from-indigo-200/80 hover:via-indigo-100/70 hover:to-slate-100/60`
    - テキスト: `from-indigo-800 via-indigo-700 to-blue-700`
    - アイコン: `text-indigo-700`
  - 廃材搬出（amber）:
    - 背景: `from-amber-100/90 via-amber-50/60 to-slate-50/70`
    - ホバー: `hover:from-amber-200/80 hover:via-amber-100/70 hover:to-slate-100/60`
    - テキスト: `from-amber-800 via-amber-700 to-orange-700`
    - アイコン: `text-amber-700`

##### 3. 状態管理の実装
- **expandedBlocksステート**: `Record<string, boolean>`形式で管理
- **toggleBlock関数**: page.tsx内で定義済み
```typescript
const toggleBlock = useCallback((blockId: string) => {
  setExpandedBlocks(prev => ({
    ...prev,
    [blockId]: !prev[blockId]
  }));
}, []);
```

##### 4. 空データ時の表示
- **表示条件**: `items.length === 0`
- **表示内容**: 
```html
<div className="text-center text-gray-500 py-8">
  項目データがありません
</div>
```
- **表示位置**: ブロック展開時の内部コンテンツエリア

##### 5. 既存コンポーネントとの関係
- **第3-5段階からBaseEstimateBlockを使用**
  - 擁壁・舗装見積ページと同じプロフェッショナルなテーブル表示
  - 撤去工事専用の色設定はpropsで指定
  - 内訳/集計タブ機能もそのまま活用

#### 実装完了時の状態
- 3つのブロック（カッター工事、撤去工事、廃材搬出）が正しい色で表示される
- 各ブロックの展開/折りたたみが個別に動作する
- 展開時は「項目データがありません」が中央に表示される
- ブロックヘッダーに小計（0円）が表示される

---

### 第3段階：計算ロジックとの連携（6つのステップに細分化）

第3段階は実装が複雑なため、6つの小さなステップに分解して実装します。各ステップは確実に動作確認してから次に進んでください。

---

### 第3-1段階：価格データのエラーハンドリング 🎯難易度: 18/100

#### 目標
CSVファイルが存在しない場合でもアプリがエラーで停止しないようにする。

#### タスク
- `/app/utils/priceData.ts`の`loadPriceData`関数を修正
- `if (!response.ok)`の処理でthrowせずに空配列を返す
- catchブロックでもthrowせずに空配列を返す

#### 実装完了時のチェック項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. http://192.168.0.39:3000/estimates/demolition にアクセス
2. ページが正常に表示される（エラー画面にならない）
3. 既存の見積もりが表示される

問題なければOKです！」
```

---

### 第3-2段階：カッター工事の計算と表示 🎯難易度: 45/100

#### 目標
page.tsx内で計算を行い、カッター工事の計算結果を画面に表示する。

#### タスク
- page.tsx内にgenerateUpdatedBlocks関数を実装
- カッター工事の計算ロジックを直接実装
- カッター工事の計算結果をEstimateItem形式に変換
- DemolitionEstimateBlockで項目名と金額のみ表示（シンプル表示）
- console.logで計算結果の構造も確認（デバッグ用）

#### 実装完了時のチェック項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. http://192.168.0.39:3000/demolition-input にアクセス
2. 新しいテストデータを入力（距離:10m, 幅:5m, 厚さ:0.3m, カッターピッチ:2m）
3. 保存して http://192.168.0.39:3000/estimates/demolition へ移動
4. 作成した見積もりをクリックして展開
5. 紫色の'カッター工事'ブロックをクリック
6. 'カッター'という項目と金額が表示される
7. F12キーでコンソールを開き、計算結果の詳細も確認できる

項目が表示されていればOKです！」
```

---

### 第3-3段階：全ブロックの基本変換 🎯難易度: 63/100

#### 目標
残りの2ブロック（撤去工事、廃材搬出）も同様に変換して表示する。

#### タスク
- generateUpdatedBlocks関数に撤去工事の計算ロジックを追加
- generateUpdatedBlocks関数に廃材搬出の計算ロジックを追加
- 撤去工事の計算結果をEstimateItem形式に変換（2行：バックホー行と使用機種行）
- 廃材搬出の計算結果をEstimateItem形式に変換（2行：残土搬出車両行と生コン行）
- 各ブロックのtotalAmountを正しく計算

#### 実装完了時のチェック項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. 先ほど作成した見積もりの3つのブロックを全て展開
2. インディゴ色の'撤去工事'ブロック：2行が表示される（バックホー行と使用機種行）
3. アンバー色の'廃材搬出'ブロック：2行が表示される（残土搬出車両行と生コン行）
4. 各ブロックのヘッダーに小計金額が表示される

全てのブロックに項目が表示されていればOKです！」
```

---

### 第3-4段階：3カラム詳細表示 🎯難易度: 68/100

#### 目標
擁壁見積ページと同じテーブル形式で、材料費・労務費・機械経費を分けて詳しく表示する。

#### タスク
- DemolitionEstimateBlockを削除し、BaseEstimateBlockを使用するように変更
- 擁壁見積ページと同じテーブルレイアウトを実装
- 各項目の数量、単位、単価、金額を表示
- ヘッダー行と合計行を追加
- 撤去工事用の色設定を追加（紫、インディゴ、アンバー）

#### 実装完了時のチェック項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. 各ブロックを展開
2. 表形式で以下の列が表示される：
   - 項目名
   - 材料費（数量×単価＝金額）
   - 労務費（数量×単価＝金額）  
   - 機械経費（数量×単価＝金額）
3. 最下部に合計行がある

擁壁見積ページと同じプロフェッショナルなテーブル表示になっていればOKです！」
```

---

### 第3-5段階：TruncatedTextWithTooltip実装 🎯難易度: 28/100

#### 目標
長い名称を省略表示し、マウスホバーで全文を表示する。

#### タスク
- TruncatedTextWithTooltipコンポーネントを作成（または既存のものを使用）
- DemolitionEstimateBlockV2で項目名に適用（テーブル表示の名称部分）
- 12文字を超える名称は「...」で省略
- 内訳表示と集計表示の両方で適用

#### 実装完了時のチェック項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. 撤去工事ブロックまたは廃材搬出ブロックを展開
2. 'バックホー0.7BH'のような長い名前を探す
3. 名前が'バックホー0...'のように省略されている
4. その名前の上にマウスを置く（クリックしない）
5. 0.5秒待つと、黒い吹き出しで全文が表示される
6. 集計タブに切り替えても同様に動作する

省略と吹き出しが動作すればOKです！

🎉 第3段階が全て完了しました！」
```

---

### 第4段階：各見積データの小計表示（8カード表示）の実装

#### 目標
擁壁見積ページと同じ8カード表示（4列×2行）で各見積の集計情報を表示する。

#### タスク
- 既存の擁壁見積ページの小計表示構造を分析
- EstimateSummaryViewコンポーネントを使用して8カード表示を実装
- 上段4カード：材料費、労務費、機械経費、直接工事費
- 下段4カード：見積もり数量、11%入力単価/m、9%小計、20%単価
- レスポンシブデザインの調整

#### 確認項目
```
- 各見積カード内に8つの小計カードが表示される（4×2グリッド）
- 上段：材料費、労務費、機械経費、直接工事費
- 下段：見積もり数量、11%入力単価/m、9%小計、20%単価
- モバイルでも適切に表示される
```

#### 実装時のメモ
- 擁壁見積ページの実装を参考にする
- 各カードの背景色、アイコン、レイアウトを統一
- 見積もり数量の計算方法を明確にする
- 単価計算のロジックを正確に実装
- **重要**：内訳・集計タブは第3-6段階で実装済みの各ブロック内のタブのみを使用
- **重要**：見積データレベルでの内訳・集計切り替えボタンは追加しない
- **重要**：編集・印刷ボタンは既存の位置（見積カードヘッダー）のままとする

---

### 第5段階：調整値機能の実装

#### 目標
調整値の設定・保存・読込機能を実装し、金額調整を可能にする。

#### タスク
- adjustmentKeysをSTATIC_ADJUSTMENT_KEYSと完全一致させる（英語統一版）
- useDemolitionAutoSave.tsを新規作成（useRetainingWallAutoSaveを参考に）
- supabaseDataService.tsの型定義に'demolition'を追加
- 調整値入力UIの実装
- 内訳モード/集計モードでの調整値表示の違いを実装
- 調整値の永続化（Supabase保存）
- 調整後金額の計算と表示

#### 確認項目
```
- 調整値を入力できる
- 調整値を変更すると金額が更新される
- 保存→リロードで調整値が保持される
- モード切替で表示が適切に変わる
- adjustmentKeysのエラーが発生しない
```

---

### 第6段階：単位切替機能の実装（m/㎡）🎯難易度: 55/100

#### 目標
集計モードでの行単位のm/㎡切替機能とサマリーカードの単位切替機能を実装する。他の見積ページ（擁壁、舗装、2次製品）と統一された操作感を提供する。

#### ⚠️ 撤去工事見積の特殊性と実装方針

**重要**: 撤去工事見積は動的ブロック生成を行うため、2次製品見積とは異なる実装方法が必要です。

##### 動的ブロック生成パターンの理解
```typescript
// 撤去工事見積の特徴
- estimate.items は常に空配列（データは保存しない）
- generateUpdatedBlocks関数で毎回動的にブロックを生成
- unitMode情報はestimate.data.unitModesで別管理

// 2次製品見積との違い
2次製品: estimate.items[0].unitMode = '㎡' // itemsに直接保存
撤去工事: estimate.data.unitModes[itemId] = '㎡' // 別オブジェクトで管理
```

#### タスク

##### 6-1. データ構造の拡張
**ファイル**: `/app/utils/types.ts`

```typescript
// EstimateItem型を拡張（既存の定義に追加）
export interface EstimateItem {
  // 既存のフィールド...
  
  // 単位モードフィールド（オプショナル）
  unitMode?: 'm' | '㎡';  // undefined の場合は 'm' として扱う
}

// EstimateData型を拡張
export interface EstimateData {
  // 既存のフィールド...
  
  // サマリーカードの単位モード
  summaryUnitMode?: 'm' | '㎡';  // undefined の場合は 'm' として扱う
  
  // 各アイテムの単位モード（撤去工事で使用）
  // 動的ブロック生成のため、itemIdをキーとしてunitModeを管理
  unitModes?: {
    [itemId: string]: 'm' | '㎡';
  };
}
```

##### 6-2. ブロック生成時のunitMode復元
**ファイル**: `page.tsx`内の`generateUpdatedBlocks`関数

```typescript
// generateUpdatedBlocks関数の最後に以下を追加
// 保存されたunitMode情報を復元
if (estimateData.unitModes && typeof estimateData.unitModes === 'object') {
  blocks.forEach((block: any) => {
    if (block.items && Array.isArray(block.items)) {
      block.items.forEach((item: any) => {
        if (item.id && estimateData.unitModes[item.id]) {
          item.unitMode = estimateData.unitModes[item.id];
        } else {
          item.unitMode = 'm'; // デフォルト値
        }
      });
    }
  });
}

return blocks;
```

##### 6-3. 集計モードでの単位切替UI実装
**ファイル**: `/app/components/demolition/DemolitionEstimateBlockV2.tsx`

```typescript
// 必要なインポートの追加
import { AnimatePresence, motion } from 'framer-motion';

// 平米計算関数
const calculateSquareMeter = (itemDistance: number = distance): number => {
  const width = estimate?.data?.width || 1.0;
  return itemDistance * width;  // 撤去工事の計算式: 距離 × 幅
};

// 単位切替ハンドラー
const toggleUnitMode = (itemId: string) => {
  if (!onUpdateItems) {
    console.warn('onUpdateItems handler not provided');
    return;
  }
  
  const currentItems = block?.items || items || [];
  const updatedItems = currentItems.map((item: EstimateItem) => {
    if (item.id === itemId) {
      const newMode = item.unitMode === '㎡' ? 'm' : '㎡';
      return { ...item, unitMode: newMode };
    }
    return item;
  });
  
  // 更新されたブロックを親コンポーネントに渡す
  const updatedBlock = {
    ...block,
    id,
    name,
    items: updatedItems
  };
  
  onUpdateItems([updatedBlock]);
};

// 集計モードでの見積数量セルの実装
<div 
  className="px-4 py-3 text-center border-r border-indigo-100/40 font-bold cursor-pointer hover:bg-blue-50 transition-all duration-300 relative group"
  onClick={() => toggleUnitMode(item.id || `item-${itemIndex}`)}
  title="クリックで単位を切り替え（m ↔ ㎡）"
>
  <AnimatePresence mode="wait">
    <motion.div
      key={item.unitMode || 'm'}
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 5 }}
      transition={{ duration: 0.2 }}
    >
      {item.unitMode === '㎡' 
        ? `${calculateSquareMeter().toFixed(2)} ㎡`
        : `${distance.toFixed(1)} m`
      }
    </motion.div>
  </AnimatePresence>
  {/* ホバー時の下線アニメーション */}
  <div className="absolute inset-0 pointer-events-none">
    <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-400 to-cyan-400 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300" />
  </div>
</div>

// 11%入力単価セルも同様に実装（クリック可能、アニメーション付き）
<div 
  className="px-4 py-3 text-center border-r border-indigo-100/40 bg-indigo-50/20 cursor-pointer hover:bg-blue-50 transition-all duration-300 relative group"
  onClick={() => toggleUnitMode(item.id || `item-${itemIndex}`)}
  title="クリックで単位を切り替え（m ↔ ㎡）"
>
  <AnimatePresence mode="wait">
    <motion.div
      key={item.unitMode || 'm'}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex items-center justify-center gap-1">
        <CurrencyWithTooltip 
          value={unitPrice11Percent} 
          formula={`${itemTotal} ÷ ${displayQuantity.toFixed(item.unitMode === '㎡' ? 2 : 1)} ÷ 0.89`} 
        />
        <span className="text-xs text-gray-600">/{item.unitMode === '㎡' ? '㎡' : 'm'}</span>
      </div>
    </motion.div>
  </AnimatePresence>
  {/* ホバー時の下線アニメーション */}
  <div className="absolute inset-0 pointer-events-none">
    <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-400 to-blue-400 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300" />
  </div>
</div>

// 9%小計と20%単価にもクリックハンドラーとアニメーションを追加
<div 
  className="px-4 py-3 text-center border-r border-indigo-100/40 cursor-pointer hover:bg-blue-50 transition-all duration-300 relative group"
  onClick={() => toggleUnitMode(item.id || `item-${itemIndex}`)}
  title="クリックで単位を切り替え（m ↔ ㎡）"
>
  <AnimatePresence mode="wait">
    <motion.div
      key={item.unitMode || 'm'}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2 }}
    >
      <CurrencyWithTooltip 
        value={subtotal9Percent} 
        formula={`${unitPrice11Percent} × ${displayQuantity.toFixed(item.unitMode === '㎡' ? 2 : 1)}`} 
      />
    </motion.div>
  </AnimatePresence>
  <div className="absolute inset-0 pointer-events-none">
    <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-400 to-cyan-400 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300" />
  </div>
</div>
```

##### 6-4. ブロックヘッダーの両単位表示
**ファイル**: `DemolitionEstimateBlockV2.tsx`のヘッダー部分

```typescript
// ブロックヘッダーに両単位を常に表示
<div className="flex items-center gap-4">
  {/* 見積数量(m) - グレー配色 */}
  <div className={`flex flex-col items-end transition-all duration-300 ${
    displayMode === 'summary' 
      ? 'transform scale-105 bg-gray-50 shadow-sm rounded-lg p-1.5 border border-gray-200' 
      : 'opacity-70'
  }`}>
    <span className="text-gray-600 text-xs">見積数量(m)</span>
    <span className="text-gray-700 font-semibold">{distance.toFixed(1)} m</span>
  </div>
  
  {/* 見積数量(㎡) - ティール配色 */}
  <div className={`flex flex-col items-end transition-all duration-300 ${
    displayMode === 'summary' 
      ? 'transform scale-105 bg-teal-50 shadow-sm rounded-lg p-1.5 border border-teal-100' 
      : 'opacity-70'
  }`}>
    <span className="text-teal-600 text-xs">見積数量(㎡)</span>
    <span className="text-teal-700 font-semibold">{calculateSquareMeter().toFixed(2)} ㎡</span>
  </div>
</div>
```

##### 6-5. サマリーカードの単位切替
**ファイル**: `page.tsx`

```typescript
// サマリーカードの単位モード管理（各見積ごと）
const [summaryUnitModes, setSummaryUnitModes] = useState<Record<string, 'm' | '㎡'>>({});

// 既存データから復元
useEffect(() => {
  const modes: Record<string, 'm' | '㎡'> = {};
  savedEstimates.forEach(est => {
    modes[est.id] = est.data?.summaryUnitMode || 'm';
  });
  setSummaryUnitModes(modes);
}, [savedEstimates]);

// サマリーカード切替ハンドラー
const handleToggleSummaryUnit = useCallback((estimateId: string) => {
  const currentMode = summaryUnitModes[estimateId] || 'm';
  const newMode = currentMode === '㎡' ? 'm' : '㎡';
  
  setSummaryUnitModes(prev => ({
    ...prev,
    [estimateId]: newMode
  }));
  
  // estimate.dataに保存
  setSavedEstimates(prev => prev.map(est => {
    if (est.id === estimateId) {
      return {
        ...est,
        data: {
          ...est.data,
          summaryUnitMode: newMode
        }
      };
    }
    return est;
  }));
}, [summaryUnitModes]);

// EstimateSummaryViewに渡す
<EstimateSummaryView
  estimate={estimate}
  blocks={blocks}
  materialTotalAll={materialTotalAll}
  laborTotalAll={laborTotalAll}
  machineTotalAll={machineTotalAll}
  grandTotalAll={grandTotalAll}
  summaryUnitMode={summaryUnitModes[estimate.id] || 'm'}
  onToggleSummaryUnit={() => handleToggleSummaryUnit(estimate.id)}
  estimateType="demolition"
/>
```

##### 6-6. onUpdateItemsハンドラーの実装
**ファイル**: `page.tsx`

```typescript
// onUpdateItemsハンドラー（撤去工事特有の実装）
onUpdateItems={(updatedBlocks) => {
  setSavedEstimates(prev => prev.map(est => {
    if (est.id === estimate.id) {
      const updatedEstimate = { ...est };
      
      // unitModesフィールドを初期化
      if (!updatedEstimate.data) {
        updatedEstimate.data = {};
      }
      if (!updatedEstimate.data.unitModes) {
        updatedEstimate.data.unitModes = {};
      }
      
      // 各ブロックのアイテムからunitModeを抽出
      // 注意: itemsは保存せず、unitModesのみ保存
      updatedBlocks.forEach((updatedBlock: any) => {
        if (updatedBlock.items && Array.isArray(updatedBlock.items)) {
          updatedBlock.items.forEach((item: any) => {
            if (item.id && item.unitMode) {
              updatedEstimate.data.unitModes[item.id] = item.unitMode;
            }
          });
        }
      });
      
      return updatedEstimate;
    }
    return est;
  }));
}}
```

##### 6-7. 自動保存フックの修正
**ファイル**: `/app/hooks/useDemolitionAutoSave.ts`

```typescript
// 保存処理にunitModes情報を含める
const updatedData = {
  ...estimate.data,
  adjustments: {
    demolition: estimateAdjustments
  },
  summaryUnitMode: summaryUnitModes?.[estimate.id] || 'm',
  unitModes: estimate.data?.unitModes || {}
};

await updateEstimate(estimate.id, {
  data: updatedData
  // 注意: itemsは保存しない（常に空配列）
});

// 変更検知ロジックにunitModes変更も含める
const currentDataString = JSON.stringify({ 
  adjustments, 
  estimatesCount: filteredEstimates.length,
  // unitModes情報も変更検知に含める
  unitModes: filteredEstimates.map(est => ({
    id: est.id,
    unitModes: est.data?.unitModes || {},
    summaryMode: est.data?.summaryUnitMode || 'm'
  }))
});
```

#### 実装時の注意事項

##### ⚠️ 必ず確認すべきポイント

1. **データ構造の違いを理解する**
   - 2次製品見積：`estimate.items[0].unitMode`に直接保存
   - 撤去工事見積：`estimate.data.unitModes[itemId]`で管理

2. **動的ブロック生成での復元**
   - generateUpdatedBlocks関数の最後でunitModes情報を復元
   - アイテムIDの一貫性を保つ（generateDeterministicIdを使用）

3. **自動保存の特殊処理**
   - itemsフィールドは保存しない（常に空配列）
   - data.unitModesのみを永続化

4. **UIの統一性**
   - 4つの見積ページ全てで同じアニメーション
   - ホバー時の下線アニメーション必須
   - グレー（m）とティール（㎡）の配色統一

#### 確認項目
```
✅ 実装完了後の確認指示：
「単位切替機能の実装が完了しました。以下をチェックしてください：

【集計テーブル】
1. http://192.168.0.39:3000/estimates/demolition にアクセス
2. 見積を展開し、「集計」モードに切り替える
3. 集計テーブルの「見積数量」「11%入力単価」「9%小計」「20%単価」のいずれかをクリック
4. クリックした行のみ単位がm→㎡に切り替わる（他の行は影響なし）
5. 平米計算が正しい（距離 × 幅）
6. 値切替時にアニメーションが表示される
7. ホバー時に青〜シアンのグラデーション下線が左から右に展開される

【サマリーカード】
8. ページ下部の「見積もり数量」「11%入力単価」「9%小計」「20%単価」のいずれかをクリック
9. 4つのカード全てが同時に切り替わる
10. ホバー時に4枚全てにグラデーションボーダー（35%透明度）が表示される
11. 切替時に数値がアニメーションする

【永続化】
12. 単位を切り替えた後、ページをリロード（F5）
13. 切り替えた単位設定が全て維持されている
14. 自動保存インジケーターが正しく動作する

【他ページとの統一性】
15. 擁壁、舗装、2次製品見積と全く同じ操作感である」
```

---

## ⚠️ 実装上の重要な注意事項

### 1. データ保存の原則
- **items は常に空配列で保存する**
- 表示時に generateBlocksFromEstimate で動的生成する
- 詳細は [データフロー仕様](./5_data-flow.md) を参照

### 2. adjustmentKeys の管理
- 必ず `/app/constants/staticAdjustmentKeys.ts` の定義と完全一致させる
- スペルミスは致命的なエラーになるので要注意

### 3. 計算ロジックの実装
- 擁壁見積ページのgenerateUpdatedBlocks関数の構造を参考にする
- 計算ロジックはpage.tsx内に直接実装する
- DemolitionCalculator.tsは印刷ページ専用として残す

### 4. 既存ページとの整合性
- 擁壁見積ページの構造を完全に踏襲する
- 独自の実装は避け、既存のパターンに従う

### 5. tekkyo.txt仕様の反映
- 3ブロック構成（カッター工事、撤去工事、廃材搬出）
- カッター工事は1行（材料費のみ）
- 撤去工事は2行構成：
  - バックホー行：材料費（バックホー名表示のみ）、労務費（撤去作業員）、機械経費（バックホー）
  - 使用機種行：材料費（使用機種名表示のみ）、機械経費（使用機種）
- 廃材搬出は2行構成：
  - 残土搬出車両行：材料費（車両名表示のみ）、機械経費（残土搬出車両）
  - 生コン行：材料費（生コン、数量は搬出廃材量×1.2、単位：㎥）
    ※注意：生コンの数量は搬出廃材量(t)と同じ数値を使用し、単位表示のみ㎥に変更
- 常用ダンプは存在しない（tekkyo.txtに記載なし）

## 📚 関連ドキュメント

- [1_overview.md](./1_overview.md) - 撤去工事見積ページの概要
- [2_input-page.md](./2_input-page.md) - 入力ページの仕様
- [3_calculations.md](./3_calculations.md) - 計算ロジックの詳細
- [4_implementation-guide.md](./4_implementation-guide.md) - 技術的な実装ガイド
- [5_data-flow.md](./5_data-flow.md) - データフローの仕様

---

**このドキュメントは実装の進捗に応じて更新してください。**