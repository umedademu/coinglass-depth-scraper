# Depth Viewer Web版 実装計画

## 📌 このドキュメントについて

これはBTC-USDT板情報をブラウザで表示するWebアプリケーション（https://depth-viewer.vercel.app/）の実装計画書です。
各段階で動作確認を行いながら、確実に機能を積み上げていく開発手法を採用しています。

**重要**: 実装を始める前に、必ずこのドキュメント全体を読んでください。

### 開発ブランチについて
- **開発ブランチ**: `refactor/unified-chart`
- **重要**: 開発中のコミットは必ず `refactor/unified-chart` ブランチにpushしてください
- mainブランチへのマージは全段階完了後に行います

## 🎯 実装方針

1. **段階的実装**: 8つの段階に分けて、各段階で動作確認を行う
2. **既存資産の活用**: Pythonアプリのデザインと計算ロジックを踏襲
3. **認証なし**: URLを知っていれば誰でも閲覧可能（第1版）
4. **モバイルファースト**: レスポンシブデザインで全デバイス対応
5. **UI配置の原則**: 
   - 現在の市場情報を最上部に配置（価格、板の状態など）
   - タイムフレーム選択をその下に配置
   - グラフをメインコンテンツとして中央に配置
   - 詳細データテーブルを最下部に配置

## 📍 実装の前提条件

**重要**: 実装を開始する前に、以下の前提条件を確認してください：

### データベース環境
- Supabaseプロジェクト「depth」が稼働中
- **Supabase MCPツール使用時**: 必ずプロジェクトID `rijqtostuemonbfcntck` を使用すること
- 以下のテーブルが存在し、データが継続的に追加されている：
  - `order_book_shared` - 5分足データ
  - `order_book_15min` - 15分足データ
  - `order_book_30min` - 30分足データ
  - `order_book_1hour` - 1時間足データ
  - `order_book_2hour` - 2時間足データ
  - `order_book_4hour` - 4時間足データ
  - `order_book_daily` - 日足データ
- 各テーブルには以下のカラムが存在：
  - `id`, `timestamp`, `ask_total`, `bid_total`, `price`, `group_id`
- group_idは「default-group」で統一
- **API制限**: 1リクエストあたり最大1000行まで（無料・有料プラン共通）
- **各時間足での補完可能期間（1000行制限）**:
  - 5分足: 約3.5日分
  - 15分足: 約10.4日分
  - 30分足: 約20.8日分
  - 1時間足: 約41.7日分
  - 2時間足: 約83.3日分
  - 4時間足: 約166.7日分
  - 日足: 約2.7年分

### デスクトップアプリ
- Pythonスクレーパーが5分ごとにデータを収集
- 各時間足のデータを事前集約してアップロード済み
- 詳細は[デスクトップアプリ仕様書](./desktop-app-spec.md)を参照

### 開発環境
- Node.js 18以上がインストール済み
- Vercelアカウントが設定済み
- GitHubリポジトリと連携済み

## 📋 実装段階

**重要な変更（2025-01-19）**: 
- 第3段階: 2つの独立グラフ → 1つの統合グラフ
- 第4段階: ズーム機能を前倒し（第7→第4）
- 段階を8つに再編成（より論理的な流れ）

### 第1段階：Supabase接続確認 🎯難易度: 15/100

#### 目標
Supabaseに接続し、データが取得できることを確認する。

#### タスク
- Supabase Anon Keyの取得と環境変数設定
- Supabaseクライアントの初期化
- デフォルト時間足（1時間足）から最新10件のデータ取得のみ
- コンソールにデータを出力

#### 確認項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. npm run dev でローカルサーバーを起動
2. http://localhost:3000 にアクセス
3. F12キーで開発者コンソールを開く
4. コンソールに以下が表示される：
   - "Supabase connected successfully"
   - 各時間足テーブルからのデータ（5分足、15分足、30分足、1時間足、2時間足、4時間足、日足）
5. エラーが表示されていない

問題なければOKです！」
```

---

### 第2段階：データ取得と表示 🎯難易度: 25/100

#### 目標
選択した時間足のデータを取得し、画面上にテーブル形式で表示する。

#### タスク
- **データ取得の実装**
  - デフォルト時間足（1時間足）のテーブルから取得
  - 最新1000件のデータを取得（初期表示用）
  - 取得後、データを時系列順（古い→新しい）にソート
- **テーブル表示の実装（確認用・一時的）**
  - テーブルコンポーネントの作成
  - 最新100件のデータをテーブルに表示
  - timestamp、売り板、買い板、価格を表示
  - 買い/売り比率の計算と表示
  - 最終更新時刻の表示
  - **注意**: このテーブルは第6段階で削除予定

#### 確認項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. http://localhost:3000 にアクセス
2. ページ上部に現在の情報が表示される：
   - 最新価格（例：$117,721）
   - 売り板総量（例：7,502 BTC）
   - 買い板総量（例：13,945 BTC）
   - 買い/売り比率（例：1.86）
3. テーブルに100行のデータが表示される
4. 各行にtimestamp、ask、bid、priceが表示される
5. タイムスタンプが日本時間で表示される

データが正しく表示されていればOKです！」
```

---

### 第3段階：統合グラフの実装 ✅完了

#### 目標
Chart.jsを使用して、売り板・買い板・価格を1つの統合グラフで表示する。垂直方向に分離された3つのエリアで各データを表示。UIは純粋なグラフのみとし、余計な装飾は一切含めない。

#### タスク
- Chart.jsライブラリのインストールと設定（chart.js、react-chartjs-2）
- **1つの統合グラフの実装（垂直分離）**
  - 3つのデータセット（売り板、買い板、価格）
  - 初期1000データポイントを表示
  - **データポイントマーカーは非表示（pointRadius: 0）**
  - テーブルは第2段階のまま維持（確認用）
  - **グラフ高さ: 800px固定**
  - **グラフのみ表示（タイトル・凡例・説明文は一切なし）**
- **データの正規化（0-100範囲）**
  - 売り板: 70-100の範囲（上部30%）
  - 価格: 30-70の範囲（中央40%）
  - 買い板: 0-30の範囲（下部30%）
- **共通スケール正規化**
  - ASKとBIDの範囲を比較し、大きい方を基準に正規化
  - `maxRange = Math.max(askRange, bidRange)`を使用
  - 1 BTCの視覚的な高さをASK/BIDで統一
- 売り板（明るい赤色 rgb(248, 113, 113)）の実装
  - **上部30%エリア、反転表示（値が大きいほど下に）**
  - **エリアチャート（塗りつぶし）、fill.target: { value: 100 }**
  - **共通スケールで正規化**
  - **yAxisID: 'y'（左側Y軸を使用）**
  - **pointRadius: 0（マーカー非表示）**
- 買い板（明るい緑色 rgb(74, 222, 128)）の実装
  - **下部30%エリア、通常表示**
  - **エリアチャート（塗りつぶし）、fill.target: { value: 0 }**
  - **共通スケールで正規化**
  - **yAxisID: 'y'（左側Y軸を使用）**
  - **pointRadius: 0（マーカー非表示）**
- 価格（オレンジ色 #ff9500）の実装
  - **中央40%エリア**
  - 線を太めに設定（borderWidth: 3）
  - 塗りつぶしなし（線グラフ）
  - **yAxisID: 'y2'（右側Y軸を使用）**
  - **pointRadius: 0（マーカー非表示）**
- **Y軸ラベルの表示仕様（2軸分離）**
  - **左側Y軸（ASK/BID用）**
    - 数字のみ表示（「BTC(売)」などの単位や説明は付けない）
    - 実データの最大値までのみラベル表示
    - 売り板: 実際の最小値～最大値の範囲でラベル表示
    - 買い板: 実際の最小値～最大値の範囲でラベル表示
    - 中央部分（30-70範囲）はラベル表示なし
  - **右側Y軸（価格用）**
    - $記号付きで表示（例: $117,000）
    - 30-70の範囲のみラベル表示
    - グリッド線は非表示（grid.display: false）
  - **共通スケールでグラフは描画するが、ラベルは実データ範囲に制限**
- **グラフUIの設定**
  - 凡例（legend）を非表示（display: false）
  - グラフタイトルなし
  - 説明パネルなし
  - 純粋なグラフコンテナのみ
- X軸（時刻）の共通化
- グリッド線とダークテーマの適用（背景: #0a0a0a、コンテナ: #1e1e1e）

#### 確認項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. http://localhost:3000 にアクセス
2. 画面中央に1つの統合グラフ（高さ800px）が表示される：
   - 売り板の推移（明るい赤色のエリアチャート、上部30%、反転表示）
   - 買い板の推移（明るい緑色のエリアチャート、下部30%、通常表示）
   - 価格の推移（オレンジ色の線、中央40%）
3. グラフの背景がダーク（#0a0a0a）
4. **3つのデータが垂直方向に分離されて表示される**
5. **売り板（上）と買い板（下）が重ならない**
6. **価格チャートが中央40%のエリアに収まっている**
7. グリッド線が薄く表示される
8. **Y軸ラベルが左右に分離して表示される：**
   - 左側Y軸: 4,746、7,317など（ASK/BID値、単位や説明なし）
   - 右側Y軸: $117,231など（価格のみ$記号付き）
9. **Y軸ラベルが実データの最大値までで制限される**
10. **グラフタイトル・凡例・説明文が一切表示されない**
11. **売り板の反転表示（値が大きいほど下に）**
12. **データポイントのマーカー（丸い点）が表示されない**
13. マウスホバーで3つの値がツールチップに表示される（実際の値）
14. グラフに約1000個のデータポイントが表示される
15. 価格線がオレンジ色で太めに表示される

グラフが正しく垂直分離され、UIが最小限になっていればOKです！」
```

---

### 第4段階：グラフ基本操作とUI整理 ✅完了

#### 目標
グラフの基本的な操作機能（ズーム・パン）を実装し、不要なテーブルを削除する。動的スケール機能により、表示範囲に応じてグラフが自動的に最適化される。

#### 設計方針（重要）
- **ReactとChart.jsの責任分離が必須**
  - React側：初期データの準備のみ（useMemoで1回だけ計算）
  - Chart.js側：ズーム/パン時の動的更新を内部で処理
  - **警告**：ズーム時にReactのstateやuseMemoを更新するとチャートが再生成されズームがリセットされる

#### 実装手順（段階的アプローチ）
1. **第1ステップ：純粋なズーム機能の実装**
   - chartjs-plugin-zoomのインストール（hammerjs含む）
   - SSR対応：`typeof window !== 'undefined'`で動的インポート
   - 動的スケール更新を含めない基本的なズーム/パン機能のみ実装
   - この段階でズーム状態が維持されることを確認

2. **第2ステップ：動的スケール更新の追加**
   - `updateDynamicScale`関数を`useCallback`で定義
   - Chart.jsインスタンスを直接操作する設計
   - `chart.data.datasets[n].data`を直接更新
   - `chart.options.scales.y.ticks.callback`を動的に書き換え
   - `chart.update('none')`でアニメーションなし更新

#### タスク
- **chartjs-plugin-zoomの設定**
  ```javascript
  // プラグインの動的インポート（SSR対応）
  let zoomPlugin: any
  if (typeof window !== 'undefined') {
    zoomPlugin = require('chartjs-plugin-zoom').default
    ChartJS.register(zoomPlugin)
  }
  ```
- **ズーム機能の実装**
  - `onZoomComplete: ({ chart }) => { updateDynamicScale(chart); setIsZoomed(true) }`
  - `onPanComplete: ({ chart }) => { updateDynamicScale(chart); setIsZoomed(true) }`
  - ズームリセットボタン（isZoomed時のみ表示）
- **動的スケール調整の実装**
  ```javascript
  const updateDynamicScale = useCallback((chart: any) => {
    // 1. 表示範囲の取得
    const xScale = chart.scales.x
    const visibleData = sortedData.slice(min, max + 1)
    
    // 2. 新しいスケール値の計算
    // 3. データセットの直接更新（Reactの再レンダリングを避ける）
    chart.data.datasets[0].data = normalizedAskData
    
    // 4. Y軸ラベルの更新
    chart.options.scales.y.ticks.callback = function(value) { /* 動的計算 */ }
    
    // 5. アニメーションなし更新
    chart.update('none')
  }, [sortedData])
  ```
- **ASK/BIDの共通スケール維持**
  - 表示範囲内のASK範囲とBID範囲を比較
  - `maxRange = Math.max(askRange, bidRange)`で統一
- **価格チャートの独立スケーリング**
  - 価格は独自の最小値・最大値で正規化
- **テーブル表示の削除**
  - OrderBookTableコンポーネントの削除
  - UIをシンプルに整理

#### 確認項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. http://localhost:3000 にアクセス
2. テーブルが削除され、グラフのみ表示される
3. マウスホイールを回転：
   - グラフが拡大・縮小される
   - スムーズにズーム動作
   - **Y軸ラベルが表示範囲に応じて動的に更新される**
   - **グラフの形状自体が拡大される（山が大きく表示）**
4. ズームリセットボタン：
   - ズーム中のみ表示される
   - クリックで全体表示に戻る
5. グラフをドラッグ（パン操作）：
   - 表示範囲が移動する
   - **ズームレベルが維持される（リセットされない）**
   - **移動した範囲に応じてグラフが再正規化される**
6. 動的スケール調整の動作：
   - **表示範囲内のデータで最小値・最大値が再計算される**
   - **グラフの山や谷が画面いっぱいに拡大表示される**
   - **細かい変動が見やすくなる**
7. ASK/BIDの共通スケール：
   - **範囲が大きい方が30%枠をフルに使用**
   - **小さい方は価格ライン側に余白が生じる**
   - **両者の相対的な大きさが正しく維持される**
8. 価格チャートの独立スケーリング：
   - **表示範囲内の価格変動が中央40%枠いっぱいに表示**
   - **細かい価格変動が見やすくなる**
9. ズーム後の状態：
   - 売り板の反転表示が維持される
   - 3つのデータが正しく表示される
   - ドラッグしてもズームが維持される

グラフ操作と動的スケール調整が正しく動作すればOKです！」
```

---

### 第5段階：タイムフレーム切り替え（遅延読み込み版） 🎯難易度: 35/100

#### 目標
時間足の切り替え機能を実装し、必要な時のみデータを取得する効率的なシステムを構築する。

#### タスク
- タイムフレーム選択ボタンの追加
- 5分足、15分足、30分足、1時間足、2時間足、4時間足、日足の選択肢
- **遅延読み込みの実装**
  - 初期表示: デフォルト時間足（1時間足）の1000件のみ取得
  - 時間足切り替え時: その時間足のデータを初めて1000件取得
  - 2回目以降: キャッシュから即座に表示
- **キャッシュ管理**
  - 各時間足ごとにデータをメモリに保持
  - ページリロードでクリア
- グラフの再描画処理
- 選択状態の保持（localStorage使用）
- UI配置の最適化（諸々の情報 → タイムフレーム → グラフ の順序）

#### 確認項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. http://localhost:3000 にアクセス
2. UIの配置順序が以下になっている：
   - 最新価格などの現在情報（最上部）
   - タイムフレーム選択ボタン（その下）
   - グラフ（その下）
3. 「5分足」を選択：
   - order_book_sharedテーブルからデータ取得
   - 5分ごとのデータポイント
4. 「15分足」を選択：
   - order_book_15minテーブルからデータ取得
   - 15分ごとのデータポイント
5. 「30分足」を選択：
   - order_book_30minテーブルからデータ取得
   - 30分ごとのデータポイント
6. 「1時間足」を選択：
   - order_book_1hourテーブルからデータ取得
   - 1時間ごとのデータポイント
7. 「2時間足」を選択：
   - order_book_2hourテーブルからデータ取得
   - 2時間ごとのデータポイント
8. 「4時間足」を選択：
   - order_book_4hourテーブルからデータ取得
   - 4時間ごとのデータポイント
9. 「日足」を選択：
   - order_book_dailyテーブルからデータ取得
   - 1日ごとのデータポイント
10. ページリロード後も選択が保持される

タイムフレーム切り替えが動作すればOKです！」
```

---

### 第6段階：リアルタイム更新 🎯難易度: 60/100

#### 目標
Supabase RealtimeでWebSocket接続し、データ更新時に自動的にグラフを更新する。

#### タスク
- Supabase Realtime購読の設定
- WebSocket接続の確立
- 新規データ受信時の処理
- グラフへのデータ追加（アニメーション付き）
- 接続状態インジケーターの表示
- 接続エラー時の再接続処理
- **基本的なメモリ管理**
  - リアルタイムデータ追加時の配列サイズ確認
  - 必要に応じて古いデータを削除

#### 確認項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. http://localhost:3000 にアクセス
2. ページ右上に接続状態が表示される：
   - 緑の●：接続中
   - 黄の●：接続中...
   - 赤の●：切断
3. 5分間ページを開いたままにする
4. 5分後に以下が自動的に起こる：
   - グラフに新しいポイントが追加される
   - 最新価格が更新される
   - ページリロードは不要
5. ネットワークを一時切断して再接続：
   - 自動的に再接続される
   - データの欠損がない

リアルタイム更新が動作すればOKです！
※Pythonスクレーパーが動作している必要があります」
```

---

### 第7段階：高度なデータ管理（無限スクロール） 🎯難易度: 65/100

#### 目標
グラフをドラッグして過去のデータを動的に取得する機能と、効率的なメモリ管理を実装する。

#### 設計方針
- **第4段階の実装基盤を活用**
  - `onPanComplete`で左端到達を検知
  - `updateDynamicScale`でデータ追加後の再スケーリング
- **X軸インデックス管理が重要**
  - データを左側に追加するとインデックスがずれる
  - 現在の表示位置を維持する処理が必須

#### タスク
- **動的データ取得の実装**
  ```javascript
  const handlePanComplete = ({ chart }) => {
    const xScale = chart.scales.x
    if (xScale.min <= 0) {
      // 左端到達を検知
      loadMoreData()
    }
  }
  ```
- **データ追加時のX軸位置調整**
  ```javascript
  const loadMoreData = async () => {
    const oldDataLength = sortedData.length
    const newData = await fetchOlderData()
    
    // データを左側に追加
    setSortedData([...newData, ...sortedData])
    
    // X軸インデックスを調整（重要）
    const chart = chartRef.current
    if (chart) {
      const addedCount = newData.length
      chart.options.scales.x.min += addedCount
      chart.options.scales.x.max += addedCount
      chart.update('none')  // 即座に反映
    }
  }
  ```
- **プリフェッチ機能**
  - 左端の80%に到達したら先読み開始
  - `xScale.min < (dataLength * 0.2)`で判定
- **ローディングインジケーター**
  - データ取得中の表示
  - グラフ上部に小さく表示
- **メモリ管理の実装**
  - 各時間足で最大5000件まで保持
  - 5000件を超えたら右端（新しいデータ）から削除
  - X軸インデックスの再調整が必要

#### 確認項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：
1. グラフをマウスでドラッグして左に移動
2. 左端に到達すると自動的に過去のデータを取得
3. ローディング中はインジケーターが表示される
4. 取得後、シームレスに過去データが表示される
5. メモリ使用量が増えすぎない（5000件制限）
6. 複数回スクロールしても動作が重くならない
7. 時間足を切り替えても各時間足で独立してメモリ管理される

動的データ取得とメモリ管理が正しく動作すればOKです！」
```

---

### 第8段階：UI/UX最終調整 🎯難易度: 40/100

#### 目標
ユーザビリティを向上させ、プロフェッショナルな見た目に最終調整する。

#### タスク
- ローディング画面の実装
- エラー画面の実装（データ取得失敗時）
- レスポンシブデザインの調整
- スマートフォン用の縦画面対応
- タブレット用の最適化
- **インタラクション改善**
  - 線ベースの当たり判定（Chart.js interaction mode: 'index', intersect: false）
  - ツールチップの改善（実データ値の表示）
  - X軸に日付変更点（0:00）で日付表示を追加
- パフォーマンス最適化

#### 確認項目
```
✅ ユーザーへの確認指示：
「実装が完了しました。以下をチェックしてください：

【デスクトップ】
1. http://localhost:3000 にアクセス
2. 初回ロード時にローディング画面が表示される
3. 全体的にプロフェッショナルな見た目

【インタラクション改善】
4. グラフ上でマウスを横に動かすと縦軸全体でデータが選択される
5. グラフのX軸をポイントしなくても、その時刻のデータが表示される
6. ツールチップではなく、画面上部のヘッダーに情報が表示される
7. X軸の0:00の位置に日付（例：01/19）が表示される

【スマートフォン】
8. スマホでアクセス（または開発者ツールでモバイル表示）
9. グラフが画面幅に収まる
10. テキストが読みやすいサイズ
11. スクロールがスムーズ
12. タップ操作が快適

【エラー処理】
13. Supabase接続を切断（環境変数を一時的に変更）
14. エラー画面が表示される
15. 「再試行」ボタンが機能する

【パフォーマンス】
16. Lighthouseスコア90以上
17. 初回表示3秒以内

全ての項目が確認できればOKです！」
```

---

## ⚠️ 実装上の重要な注意事項

### 1. 環境変数の管理
- **NEXT_PUBLIC_SUPABASE_URL**: 必須
- **NEXT_PUBLIC_SUPABASE_ANON_KEY**: 必須
- ローカルは`.env.local`、本番はVercelで設定

### 2. データの扱い
- タイムスタンプはSupabaseにJSTで保存されている（Pythonスクレーパーによる）
- **重要**: タイムスタンプ表示時はタイムゾーン変換を行わない
- group_idは「default-group」でフィルタリング
- 各時間足のデータは事前集約済み（グルーピング不要）
- **価格データ**: 各レコードの`price`フィールドを使用（すでに存在）

### 3. タイムフレーム（時間足）の設計
- **実装する時間足**: 5分足、15分足、30分足、1時間足、2時間足、4時間足、日足（7種類）
- **除外する時間足**: 1分足と3分足（デスクトップアプリのローカル専用）
- **デフォルト値**: 1時間足（中期的なトレンドを把握しやすい）
- **選択状態の保持**: LocalStorageを使用してユーザーの選択を記憶
- **データ取得方式**: 
  - 初回のみ各時間足の専用テーブルから1000件取得
  - 以降はキャッシュを使用（遅延読み込み）
  - スクロール時に追加1000件ずつ取得
- **グラフ表示仕様**:
  - 初期表示: 1000データポイント
  - 最大保持: 5000データポイント（メモリ管理）
  - データが1000未満の場合はすべて表示

### 4. パフォーマンス
- **データ取得戦略**:
  - 初期ロード: デフォルト時間足1000件のみ取得
  - 時間足切替: 初回のみ1000件取得、以降はキャッシュ使用
  - 左スクロール時: 追加で1000件ずつ取得
- **キャッシュ戦略**:
  - 各時間足ごとに独立してキャッシュ
  - ページリロードでクリア
- **メモリ管理**:
  - 各時間足で最大5000件まで保持
  - 超過時は古いデータから削除
- **グラフ表示**: 動的（初期1000件、最大5000件）
- **テーブル表示**: 第2-5段階のみ（第6段階で削除）
- **目標パフォーマンス**:
  - 初期表示: 1秒以内（1000件のみ）
  - 時間足切替: 初回1秒以内、キャッシュ時は即座
  - 追加データ取得: 1秒以内

### 5. セキュリティ
- Row Level Security (RLS)は現在無効
- 将来的に認証機能を追加する場合は有効化
- Anon Keyは公開可能（読み取り専用）

## 🔧 実装詳細

### データ取得実装

```javascript
// 時間足に応じたテーブル選択
const getTableName = (timeframe) => {
  const tables = {
    '5min': 'order_book_shared',
    '15min': 'order_book_15min',
    '30min': 'order_book_30min',
    '1hour': 'order_book_1hour',
    '2hour': 'order_book_2hour',
    '4hour': 'order_book_4hour',
    '1day': 'order_book_daily'
  };
  return tables[timeframe];
}

// データ取得（初回・追加共通）
const fetchTimeframeData = async (timeframe, count = 1000, before = null) => {
  const tableName = getTableName(timeframe);
  let query = supabase
    .from(tableName)
    .select('*')
    .eq('group_id', 'default-group')
    .order('timestamp', { ascending: false })
    .limit(count);
  
  // 過去データ取得時
  if (before) {
    query = query.lt('timestamp', before);
  }
    
  const { data, error } = await query;
  if (error) throw error;
  return data;
}
```

### キャッシュ実装

```javascript
// 時間足ごとのデータキャッシュ（拡張版）
const [dataCache, setDataCache] = useState({
  '5min': { data: [], oldestTimestamp: null },
  '15min': { data: [], oldestTimestamp: null },
  '30min': { data: [], oldestTimestamp: null },
  '1hour': { data: [], oldestTimestamp: null },
  '2hour': { data: [], oldestTimestamp: null },
  '4hour': { data: [], oldestTimestamp: null },
  '1day': { data: [], oldestTimestamp: null }
});

// 時間足切替時の処理（遅延読み込み）
const handleTimeframeChange = async (timeframe) => {
  // キャッシュチェック
  if (dataCache[timeframe].data.length > 0) {
    setDisplayData(dataCache[timeframe].data);
    return;
  }
  
  // 初回取得（1000件）
  const data = await fetchTimeframeData(timeframe, 1000);
  setDataCache(prev => ({
    ...prev,
    [timeframe]: {
      data: data,
      oldestTimestamp: data[data.length - 1]?.timestamp
    }
  }));
  setDisplayData(data);
}

// 過去データ追加取得（スクロール時）
const loadMoreData = async (timeframe) => {
  const cache = dataCache[timeframe];
  if (!cache.oldestTimestamp) return;
  
  // 追加1000件取得
  const moreData = await fetchTimeframeData(
    timeframe, 
    1000, 
    cache.oldestTimestamp
  );
  
  // メモリ管理（5000件制限）
  let newData = [...moreData, ...cache.data];
  if (newData.length > 5000) {
    newData = newData.slice(0, 5000);
  }
  
  setDataCache(prev => ({
    ...prev,
    [timeframe]: {
      data: newData,
      oldestTimestamp: moreData[moreData.length - 1]?.timestamp
    }
  }));
  setDisplayData(newData);
}
```

### 統合グラフ設定例（第4段階対応）

```javascript
// 重要：ReactとChart.jsの責任分離
// useMemoで初期データのみ計算、ズーム時の更新はChart.js内部で処理

// 初期スケールの計算（固定値として使用）
const scaleValues = useMemo(() => {
  const askRange = maxAsk - minAsk
  const bidRange = maxBid - minBid
  const maxRange = Math.max(askRange, bidRange) // 共通スケール
  return { minAsk, maxAsk, minBid, maxBid, minPrice, maxPrice, maxRange }
}, [sortedData])

// データの正規化（初期表示用）
const normalizedAskData = sortedData.map(d => {
  // ASK（売り板）: 70-100の範囲（上部30%）、反転表示、共通スケール使用
  const normalizedValue = ((d.ask_total - scaleValues.minAsk) / scaleValues.maxRange) * 30
  return 100 - normalizedValue // 反転表示
})

const normalizedBidData = sortedData.map(d => {
  // BID（買い板）: 0-30の範囲（下部30%）、共通スケール使用
  return ((d.bid_total - scaleValues.minBid) / scaleValues.maxRange) * 30
})

const normalizedPriceData = sortedData.map(d => {
  // 価格: 30-70の範囲（中央40%）
  const priceRange = scaleValues.maxPrice - scaleValues.minPrice || 1
  return ((d.price - scaleValues.minPrice) / priceRange) * 40 + 30
})

// 3つのデータセットを持つ1つのグラフ
const chartData = {
  labels: timestamps,
  datasets: [
    {
      label: '売り板',
      data: normalizedAskData,
      borderColor: 'rgb(248, 113, 113)',
      backgroundColor: 'rgba(248, 113, 113, 0.3)',
      fill: { target: { value: 100 }, above: 'rgba(248, 113, 113, 0.3)' },
      yAxisID: 'y',  // 左側Y軸
      pointRadius: 0,  // マーカー非表示
      tension: 0.1,
      originalData: sortedData.map(d => d.ask_total)  // ツールチップ用
    },
    {
      label: '買い板',
      data: normalizedBidData,
      borderColor: 'rgb(74, 222, 128)',
      backgroundColor: 'rgba(74, 222, 128, 0.3)',
      fill: { target: { value: 0 }, below: 'rgba(74, 222, 128, 0.3)' },
      yAxisID: 'y',  // 左側Y軸
      pointRadius: 0,  // マーカー非表示
      tension: 0.1,
      originalData: sortedData.map(d => d.bid_total)  // ツールチップ用
    },
    {
      label: '価格',
      data: normalizedPriceData,
      borderColor: '#ff9500',
      borderWidth: 3,
      fill: false,
      yAxisID: 'y2',  // 右側Y軸
      pointRadius: 0,  // マーカー非表示
      tension: 0.1,
      originalData: sortedData.map(d => d.price)  // ツールチップ用
    }
  ]
};

const chartOptions = {
  plugins: {
    legend: {
      display: false  // 凡例を非表示
    },
    tooltip: {
      // ツールチップで実データ値を表示
      callbacks: {
        label: function(context) {
          const originalData = context.dataset.originalData
          const value = originalData[context.dataIndex]
          const label = context.dataset.label
          if (label.includes('価格')) {
            return `${label}: $${value.toLocaleString()}`
          } else {
            return `${label}: ${value.toLocaleString()} BTC`
          }
        }
      }
    }
  },
  scales: {
    'y': {  // 左側Y軸（ASK/BID用）
      position: 'left',
      min: 0,
      max: 100,
      grid: {
        color: 'rgba(255, 255, 255, 0.1)'
      },
      ticks: {
        color: '#999',
        callback: function(value) {
          // 70-100の範囲（売り板） - 反転表示
          if (value >= 70 && value <= 100) {
            const actualValue = minAsk + ((100 - value) / 30) * maxRange
            // 実データ最大値を超える場合は表示しない
            if (actualValue > maxAsk) return ''
            return Math.round(actualValue).toLocaleString()  // 数字のみ
          }
          // 0-30の範囲（買い板）
          if (value >= 0 && value <= 30) {
            const actualValue = minBid + (value / 30) * maxRange
            // 実データ最大値を超える場合は表示しない
            if (actualValue > maxBid) return ''
            return Math.round(actualValue).toLocaleString()  // 数字のみ
          }
          // 中央部分は表示しない
          return ''
        }
      }
    },
    'y2': {  // 右側Y軸（価格用）
      position: 'right',
      min: 0,
      max: 100,
      grid: {
        display: false  // 右側Y軸のグリッドは非表示
      },
      ticks: {
        color: '#999',
        callback: function(value) {
          // 30-70の範囲（価格）のみ表示
          if (value >= 30 && value <= 70) {
            const actualValue = minPrice + ((value - 30) / 40) * (maxPrice - minPrice)
            return `$${Math.round(actualValue).toLocaleString()}`  // 価格のみ$付き
          }
          return ''
        }
      }
    }
  }
};
```

### 動的スケール調整実装（第4段階準拠）

```javascript
// 重要：Chart.js内部で動的更新、Reactの再レンダリングを避ける

// 動的スケール更新関数（Chart.jsインスタンスを直接操作）
const updateDynamicScale = useCallback((chart: any) => {
  if (!chart || !sortedData.length) return
  
  // 1. 表示範囲の取得
  const xScale = chart.scales.x
  const min = Math.max(0, Math.floor(xScale.min))
  const max = Math.min(sortedData.length - 1, Math.ceil(xScale.max))
  const visibleData = sortedData.slice(min, max + 1)
  
  // 2. 新しいスケール値の計算
  const askValues = visibleData.map(d => d.ask_total)
  const bidValues = visibleData.map(d => d.bid_total)
  const priceValues = visibleData.map(d => d.price)
  
  const minAsk = Math.min(...askValues)
  const maxAsk = Math.max(...askValues)
  const minBid = Math.min(...bidValues)
  const maxBid = Math.max(...bidValues)
  const minPrice = Math.min(...priceValues)
  const maxPrice = Math.max(...priceValues)
  
  const askRange = maxAsk - minAsk
  const bidRange = maxBid - minBid
  const maxRange = Math.max(askRange, bidRange) || 1
  
  // 3. データセットの直接更新（再レンダリングを避ける）
  const normalizedAskData = sortedData.map(d => {
    const normalizedValue = ((d.ask_total - minAsk) / maxRange) * 30
    return 100 - normalizedValue
  })
  
  chart.data.datasets[0].data = normalizedAskData
  chart.data.datasets[1].data = /* BID計算 */
  chart.data.datasets[2].data = /* 価格計算 */
  
  // 4. Y軸ラベルの動的更新
  chart.options.scales.y.ticks.callback = function(value) {
    const numValue = Number(value)
    if (numValue >= 70 && numValue <= 100) {
      const actualValue = minAsk + ((100 - numValue) / 30) * maxRange
      if (actualValue > maxAsk) return ''
      return Math.round(actualValue).toLocaleString()
    }
    // ... BID範囲の処理
  }
  
  // 5. アニメーションなし更新
  chart.update('none')
}, [sortedData])

// ズーム・パン時のコールバック設定
const chartOptions = {
  plugins: {
    zoom: {
      pan: {
        enabled: true,
        mode: 'x',
        onPanComplete: ({ chart }) => {
          updateDynamicScale(chart)
          setIsZoomed(true)
        }
      },
      zoom: {
        wheel: { enabled: true, speed: 0.1 },
        mode: 'x',
        onZoomComplete: ({ chart }) => {
          updateDynamicScale(chart)
          setIsZoomed(true)
        }
      }
    }
  }
}
```

### UI改善実装（第8段階）

```javascript
// 1. 線ベースの当たり判定（縦軸全体でツールチップ表示）
const chartOptions = {
  interaction: {
    mode: 'index',        // 縦軸全体が当たり判定
    intersect: false      // ポイント上でなくてもOK
  },
  // ...他の設定
};

// 2. ヘッダー情報表示（ツールチップの代替）
const [hoveredData, setHoveredData] = useState(null);

const chartOptions = {
  onHover: (event, activeElements) => {
    if (activeElements.length > 0) {
      const dataIndex = activeElements[0].index;
      setHoveredData({
        time: timestamps[dataIndex],
        ask: askData[dataIndex],
        bid: bidData[dataIndex],
        price: priceData[dataIndex]
      });
    }
  },
  plugins: {
    tooltip: {
      enabled: false  // ポップアップを無効化
    }
  }
};

// ヘッダー表示コンポーネント
<div className="header-info">
  <span>時刻: {hoveredData?.time || latestData.time}</span>
  <span>売り板: {hoveredData?.ask || latestData.ask}</span>
  <span>買い板: {hoveredData?.bid || latestData.bid}</span>
  <span>価格: {hoveredData?.price || latestData.price}</span>
</div>

// 3. X軸に日付表示を追加
const chartOptions = {
  scales: {
    x: {
      ticks: {
        callback: function(value, index) {
          const timestamp = timestamps[index];
          const time = timestamp.split('T')[1].substring(0, 5);
          
          // 0:00の場合は日付も表示
          if (time === '00:00') {
            const date = timestamp.split('T')[0];
            const [year, month, day] = date.split('-');
            return `${month}/${day}`;
          }
          
          return time;
        },
        autoSkip: false,
        maxRotation: 45,
        minRotation: 45
      }
    }
  }
};
```

### リアルタイム更新実装

```javascript
// Realtime購読（メモリ管理付き）
useEffect(() => {
  const channel = supabase
    .channel('order-book-changes')
    .on(
      'postgres_changes',
      {
        event: 'INSERT',
        schema: 'public',
        table: getTableName(selectedTimeframe),
        filter: `group_id=eq.default-group`
      },
      (payload) => {
        // 新規データを既存データに追加
        handleNewData(payload.new);
        
        // メモリ管理（5000件超過時に古いデータ削除）
        if (currentData.length > 5000) {
          setData(prev => prev.slice(-5000));
        }
      }
    )
    .subscribe();

  return () => {
    supabase.removeChannel(channel);
  };
}, [selectedTimeframe]);
```

## 📊 テーブル構造

```sql
-- 各テーブル共通の構造
CREATE TABLE order_book_[timeframe] (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  ask_total NUMERIC NOT NULL,
  bid_total NUMERIC NOT NULL,
  price NUMERIC NOT NULL,
  group_id VARCHAR(50) DEFAULT 'default-group',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(timestamp, group_id)
);

-- インデックス
CREATE INDEX idx_[timeframe]_timestamp ON order_book_[timeframe](timestamp DESC);
CREATE INDEX idx_[timeframe]_group_id ON order_book_[timeframe](group_id);
```

## 📚 関連ドキュメント

- [Supabase公式ドキュメント](https://supabase.com/docs)
- [Next.js公式ドキュメント](https://nextjs.org/docs)
- [Chart.js公式ドキュメント](https://www.chartjs.org/docs/)
- [chartjs-plugin-zoom公式ドキュメント](https://www.chartjs.org/chartjs-plugin-zoom/)
- [デスクトップアプリ仕様書](./desktop-app-spec.md)

---

**このドキュメントは実装の進捗に応じて更新してください。**